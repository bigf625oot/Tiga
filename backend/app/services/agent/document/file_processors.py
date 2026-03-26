import asyncio
import logging
import io
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypedDict, Literal

# 第三方依赖
from agno.media import Image
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

logger = logging.getLogger("eah.file_engine")

# --- 1. 定义强类型输出协议 ---

class ProcessedResult(TypedDict):
    """标准化输出格式，确保下游 Agent 能够稳定解析"""
    status: Literal["success", "partial", "error"]
    file_type: str
    filename: str
    content_text: Optional[str]      # 用于直接注入 Context
    media_objects: List[Any]          # 用于多模态输入 (Images, etc.)
    metadata: Dict[str, Any]
    error_msg: Optional[str]

# --- 2. 抽象基类 (接口契约) ---

class BaseProcessor(ABC):
    """
    抽象处理器：定义异步处理契约
    """
    @abstractmethod
    async def process(
        self, 
        file_bytes: bytes, 
        filename: str, 
        kb_manager: Any = None,
        **kwargs
    ) -> ProcessedResult:
        pass

    def _truncate_text(self, text: str, max_chars: int = 8000) -> str:
        """防止 Token 溢出的智能截断"""
        if len(text) <= max_chars:
            return text
        return f"{text[:max_chars]}\n\n[... 内容过长已截断，建议查阅知识库 ...]"

# --- 3. 核心策略实现 ---

class ImageProcessor(BaseProcessor):
    async def process(self, file_bytes: bytes, filename: str, kb_manager: Any = None, **kwargs) -> ProcessedResult:
        # P10 级设计：支持内存二进制流直接构建，无需写磁盘
        try:
            # 某些模型支持 base64，Agno Image 可以通过 content 传入
            image_obj = Image(content=file_bytes, filepath=filename)
            return {
                "status": "success",
                "file_type": "image",
                "filename": filename,
                "content_text": f"[图片文件: {filename}]",
                "media_objects": [image_obj],
                "metadata": {},
                "error_msg": None
            }
        except Exception as e:
            logger.error(f"Image processing failed: {filename}, error: {e}")
            return self._error_response(filename, "image", str(e))

    def _error_response(self, filename: str, ftype: str, msg: str) -> ProcessedResult:
        return {"status": "error", "file_type": ftype, "filename": filename, 
                "content_text": None, "media_objects": [], "metadata": {}, "error_msg": msg}

class TextProcessor(BaseProcessor):
    async def process(self, file_bytes: bytes, filename: str, kb_manager: Any = None, **kwargs) -> ProcessedResult:
        try:
            # 1. 自动检测编码 (生产环境建议用 charset_normalizer)
            text_content = file_bytes.decode("utf-8", errors="replace")
            
            # 2. RAG 注入 (异步执行)
            if kb_manager:
                # 假设 kb_manager.add_document 是异步的
                # 如果是物理路径，传递 path；如果是流，传递文本
                await asyncio.to_thread(kb_manager.add_text, text_content, filename)
            
            return {
                "status": "success",
                "file_type": "text",
                "filename": filename,
                "content_text": self._truncate_text(text_content),
                "media_objects": [],
                "metadata": {"char_count": len(text_content)},
                "error_msg": None
            }
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            return {"status": "error", "file_type": "text", "filename": filename, 
                    "content_text": None, "media_objects": [], "metadata": {}, "error_msg": str(e)}

class PDFProcessor(BaseProcessor):
    async def process(self, file_bytes: bytes, filename: str, kb_manager: Any = None, **kwargs) -> ProcessedResult:
        if not PdfReader:
            return {"status": "error", "file_type": "pdf", "filename": filename, "content_text": None, 
                    "media_objects": [], "metadata": {}, "error_msg": "pypdf not installed"}

        try:
            # 使用内存流处理 PDF
            reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            
            final_text = "\n".join(text_parts)

            # P10 级逻辑：扫描件检测
            if len(final_text.strip()) < 10 and len(reader.pages) > 0:
                # 此处可以触发 OCR 逻辑或返回特定标识
                final_text = f"[警告: {filename} 可能是扫描件，无法提取文本，请使用多模态模型查看图片]"

            if kb_manager:
                await asyncio.to_thread(kb_manager.add_text, final_text, filename)

            return {
                "status": "success",
                "file_type": "pdf",
                "filename": filename,
                "content_text": self._truncate_text(final_text),
                "media_objects": [],
                "metadata": {"page_count": len(reader.pages)},
                "error_msg": None
            }
        except Exception as e:
            return {"status": "error", "file_type": "pdf", "filename": filename, 
                    "content_text": None, "media_objects": [], "metadata": {}, "error_msg": str(e)}

# --- 4. 处理器工厂 (高级注册机) ---

class FileProcessorFactory:
    """
    高内聚工厂：支持动态扩展与 MIME 类型映射
    """
    _registry: Dict[str, BaseProcessor] = {}

    @classmethod
    def initialize(cls):
        """初始化默认注册表"""
        img_proc = ImageProcessor()
        cls.register(["jpg", "jpeg", "png", "webp", "gif"], img_proc)
        
        txt_proc = TextProcessor()
        cls.register(["txt", "md", "py", "js", "csv", "json", "html"], txt_proc)
        
        cls.register(["pdf"], PDFProcessor())

    @classmethod
    def register(cls, extensions: List[str], processor: BaseProcessor):
        for ext in extensions:
            cls._registry[ext.lower()] = processor

    @classmethod
    def get_processor(cls, filename: str) -> BaseProcessor:
        ext = filename.split('.')[-1].lower() if '.' in filename else ""
        # 默认返回 TextProcessor 作为兜底
        return cls._registry.get(ext, TextProcessor())

# 初始化
FileProcessorFactory.initialize()

