import shutil
import os
import json
import io
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import UploadFile
import pypdf

from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.media import Image
from agno.models.message import Message
from agno.utils.log import logger as agno_logger

# 禁用 agno 内部日志记录，以避免 "str object has no attribute log" 错误
# 这是一个针对 agno 的临时解决方案，因为它尝试将字符串消息作为对象记录
import logging
logging.getLogger("agno").setLevel(logging.WARNING)

from app.core.config import settings
from app.models.llm_model import LLMModel
from app.models.knowledge import KnowledgeDocument
from app.services.model_factory import ModelFactory
from app.services.oss_service import oss_service
from app.services.lightrag_service import lightrag_service
from app.services.document_parser import parse_local_file
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

# 路径配置
# Fix: Use relative path "data" instead of "backend/data"
DATA_DIR = Path("data")
LANCEDB_DIR = DATA_DIR / "lancedb"
UPLOAD_DIR = DATA_DIR / "uploads"

# 确保必要的目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LANCEDB_DIR.mkdir(parents=True, exist_ok=True)

class KnowledgeBaseService:
    """
    知识库服务类，负责管理向量数据库、文档索引和知识图谱提取。
    实现了单例模式。
    """
    _instance = None

    def __init__(self):
        # 默认配置（从环境变量加载）
        self._init_default()

    def _init_default(self):
        """
        初始化默认配置，包括 Embedder 和向量数据库。
        支持通过环境变量配置 OpenAI 或 DeepSeek。
        """
        # 配置 Embedder (支持通过 OpenAI 兼容接口使用 DeepSeek)
        embedder_config = {
            "api_key": settings.OPENAI_API_KEY or "dummy",
            "id": "openai-embedding",
            "dimensions": 1536
        }
        
        # 如果存在 DeepSeek 设置，覆盖默认配置
        if settings.DEEPSEEK_API_KEY:
            embedder_config["api_key"] = settings.DEEPSEEK_API_KEY
            embedder_config["base_url"] = settings.DEEPSEEK_BASE_URL
            embedder_config["id"] = "deepseek-embed"
            embedder_config["dimensions"] = 1024

        # 生成唯一的表名，避免不同维度的向量混用
        table_name = f"vectors_{embedder_config.get('id','embed')}_{embedder_config.get('dimensions',1536)}"

        # 初始化 LanceDb 向量数据库
        self.vector_db = LanceDb(
            table_name=table_name,
            uri=str(LANCEDB_DIR),
            embedder=OpenAIEmbedder(**embedder_config)
        )
        
        # 初始化 Knowledge 对象
        self.knowledge = Knowledge(
            name="Recorder Knowledge Base",
            vector_db=self.vector_db,
        )

    @classmethod
    def get_instance(cls):
        """
        获取单例实例。
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def reload_config(self, db: AsyncSession):
        """
        从数据库重新加载配置（主要用于更新 Embedder 模型设置）。
        当用户在前端更改了嵌入模型配置时调用。
        """
        try:
            # 查找活跃的嵌入模型
            result = await db.execute(
                select(LLMModel)
                .filter(LLMModel.model_type == "embedding", LLMModel.is_active == True)
                .order_by(LLMModel.updated_at.desc())
            )
            model = result.scalars().first()
            
            if model:
                logger.info(f"正在使用嵌入模型重新加载知识库: {model.name} ({model.model_id})")
                
                embedder_config = {
                    "api_key": model.api_key,
                    "id": model.model_id,
                }
                
                if model.base_url:
                    embedder_config["base_url"] = model.base_url
                
                # 特殊处理：针对 BigModel (智谱) 等特定提供商的 URL 规范化
                base = (embedder_config.get("base_url") or "").lower()
                mid = (embedder_config.get("id") or "").lower()
                if "open.bigmodel.cn" in base:
                    base_norm = base.replace("/v4/embeddings", "/v4").rstrip("/")
                    embedder_config["base_url"] = base_norm
                    if mid.startswith("embedding-3"):
                        embedder_config["dimensions"] = 2048
                else:
                    embedder_config.setdefault("dimensions", 1536)
                
                table_name = f"vectors_{embedder_config.get('id','embed')}_{embedder_config.get('dimensions',1536)}"
                self.vector_db = LanceDb(
                    table_name=table_name,
                    uri=str(LANCEDB_DIR),
                    embedder=OpenAIEmbedder(**embedder_config)
                )
                self.knowledge = Knowledge(
                    name="Recorder Knowledge Base",
                    vector_db=self.vector_db,
                )
            else:
                logger.info("数据库中未找到活跃的嵌入模型，保持默认配置。")
                
        except Exception as e:
            logger.error(f"重新加载知识库配置失败: {e}")

    def index_document(self, file_path: str):
        """
        将本地文件索引到知识库中（向量化存储 + LightRAG）。
        """
        logger.info(f"Starting index_document for file: {file_path}")
        try:
            # 1. LanceDB 向量索引 (保留原有逻辑)
            logger.info("Adding content to LanceDB...")
            self.knowledge.add_content(path=file_path)
            logger.info("LanceDB indexing completed.")
            
            # 2. LightRAG 索引 (新增 Refined 逻辑)
            # 使用统一的 document_parser 读取文件内容
            path_obj = Path(file_path) # 重新定义 path_obj
            logger.info(f"开始读取文件内容用于 LightRAG: {file_path}")
            try:
                text = parse_local_file(file_path)
                logger.info(f"文件读取成功，长度: {len(text)}")
            except Exception as read_err:
                logger.error(f"LightRAG 读取文件失败: {read_err}")
                import traceback
                logger.error(traceback.format_exc())
                raise read_err # 重新抛出异常以便上层捕获
                
            if text:
                logger.info(f"正在将文档插入 LightRAG: {path_obj.name}")
                try:
                    lightrag_service.insert_text(text, description=f"Document: {path_obj.name}")
                    logger.info("LightRAG 插入成功")
                except Exception as lr_err:
                    logger.error(f"LightRAG insert_text 内部错误: {lr_err}")
                    import traceback
                    logger.error(traceback.format_exc())
                    raise lr_err
            else:
                logger.warning("文件内容为空，跳过 LightRAG 插入")
            
            return True
        except Exception as e:
            logger.error(f"索引文档失败 {file_path}: {e}")
            raise e

    def search(self, query: str, allowed_names: Optional[List[str]] = None, min_score: float = 0.0, top_k: int = 5):
        """
        在知识库中搜索相关内容。
        :param query: 搜索查询文本
        :param allowed_names: 限制搜索的文件名列表（权限控制）
        :param min_score: 最小相似度分数
        :param top_k: 返回结果数量
        """
        refs: List[Dict[str, Any]] = []
        filtered: List[Dict[str, Any]] = []
        try:
            results = self.vector_db.search(query, limit=top_k)
            for r in results:
                # 统一处理不同格式的返回结果（字典或对象）
                meta = None
                name = None
                score = 0.0
                content = None
                if isinstance(r, dict):
                    meta = r.get("metadata") or {}
                    name = (meta.get("name") or meta.get("filename") or r.get("name"))
                    score = r.get("score") or 0.0
                    content = r.get("content") or meta.get("text")
                else:
                    meta = getattr(r, "metadata", {}) or {}
                    name = meta.get("name") or meta.get("filename") or getattr(r, "name", None)
                    score = getattr(r, "score", 0.0) or 0.0
                    content = getattr(r, "content", None) or meta.get("text")
                
                # 过滤逻辑
                if allowed_names and name and name not in allowed_names:
                    filtered.append({"title": name, "score": score})
                    continue
                if score is not None and score < (min_score or 0.0):
                    filtered.append({"title": name, "score": score})
                    continue
                
                refs.append({
                    "title": name or "",
                    "url": (meta or {}).get("url"),
                    "page": (meta or {}).get("page"),
                    "score": score,
                    "preview": (content or "")[:200]
                })
        except Exception as e:
            logger.warning(f"搜索错误: {e}")
        return refs, filtered

    def delete_document(self, filename: str):
        """
        从向量数据库中删除指定文档。
        """
        try:
            # 尝试按名称删除（通常是文件名）
            self.knowledge.vector_db.delete_by_name(filename)
        except Exception as e:
            logger.error(f"删除文档失败 {filename}: {e}")
            pass 
        return {"status": "deleted"}

    async def _extract_subgraph(self, text: str, model_config: LLMModel) -> Dict[str, Any]:
        """
        辅助函数：调用 LLM 从文本块中提取子图谱。
        :param text: 文本切片
        :param model_config: LLM 模型配置
        :return: 包含 nodes 和 edges 的字典
        """
        llm = ModelFactory.create_model(model_config)
        
        # 提示词工程：要求 LLM 提取实体、关系及详细属性
        prompt = f"""
You are a knowledge graph extractor. Extract key entities (nodes) and relationships (edges) from the following text.
Return ONLY a valid JSON object (no markdown, no thinking) with the following structure:
{{
  "nodes": {{
    "node_id_1": {{
        "name": "Entity Name", 
        "type": "Person/Location/Concept", 
        "attributes": {{
            "role": "CEO", 
            "date": "2023-01-01", 
            "description": "..."
        }}
    }},
    ...
  }},
  "edges": {{
    "edge_id_1": {{"source": "node_id_1", "target": "node_id_2", "label": "relationship_type"}},
    ...
  }}
}}
Limit to top 30 most important entities and relationships. Ensure source/target IDs exist in nodes.
Do NOT use "Concept A", "Concept B" or similar generic names. Extract REAL entities from the text.
Extract rich attributes for each entity where possible (e.g. timestamps, roles, values, status).

Text:
{text}
        """
        try:
            from agno.models.message import Message
            # 暂时禁用 Agno 日志以避免错误
            import logging
            logging.getLogger("agno").setLevel(logging.WARNING)
            
            # 显式构造 Message 对象列表，避免字符串处理错误
            messages = [Message(role="user", content=prompt)]
            response = llm.response(messages=messages)
            
            content = ""
            # 兼容处理不同类型的 LLM 响应（对象、字符串、流式迭代器）
            if hasattr(response, "content"):
                content = response.content or ""
            elif isinstance(response, str):
                content = response
            elif hasattr(response, "__iter__"):
                try:
                    chunks = []
                    for chunk in response:
                        if hasattr(chunk, "content"):
                            chunks.append(str(chunk.content or ""))
                        elif isinstance(chunk, str):
                            chunks.append(chunk)
                        else:
                            chunks.append(str(chunk))
                    content = "".join(chunks)
                except Exception:
                    content = str(response)
            else:
                try:
                    content = str(response)
                except:
                    content = ""
            
            logger.debug(f"LLM Chunk Response (First 200 chars): {content[:200]}...")

            # 清洗思考过程内容 (针对 DeepSeek R1 等模型)
            if "<think>" in content and "</think>" in content:
                content = content.split("</think>")[-1].strip()
            
            # 清洗 Markdown 格式
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
            
            content = content.strip()
            
            try:
                graph_data = json.loads(content)
                return graph_data
            except json.JSONDecodeError as je:
                logger.error(f"Chunk JSON 解析错误: {je}")
                return {}
                
        except Exception as e:
            logger.error(f"子图提取错误: {e}")
            import traceback
            traceback.print_exc()
            return {}

    async def get_document_graph_local(self, db: AsyncSession, doc_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取知识图谱数据。
        
        [Refined Update]
        不再针对单文档进行昂贵的暴力 LLM 提取。
        而是返回 LightRAG 构建的高效全局图谱（或其子集）。
        这极大地降低了资源消耗并提高了响应速度。
        """
        try:
            logger.info(f"获取图谱数据 (LightRAG Mode) for doc_id: {doc_id}")
            # 使用 LightRAG 的全局图谱
            # 由于 LightRAG 是全局优化的，我们返回全局最核心的实体和关系
            import asyncio
            graph_data = await asyncio.to_thread(lightrag_service.get_graph_data)
            return graph_data
            
        except Exception as e:
            logger.error(f"获取图谱失败: {e}")
            return {"nodes": {}, "edges": {}}

    def _get_fallback_graph(self, filename: str) -> Dict[str, Any]:
        """
        当 LLM 失败时生成确定性的模拟图谱数据。
        """
        return {
            "nodes": {
                "n1": {"name": filename or "Document", "type": "File"},
                "n2": {"name": "Concept A", "type": "Entity"},
                "n3": {"name": "Concept B", "type": "Entity"},
                "n4": {"name": "Topic C", "type": "Topic"},
            },
            "edges": {
                "e1": {"source": "n1", "target": "n2", "label": "mentions"},
                "e2": {"source": "n2", "target": "n3", "label": "relates_to"},
                "e3": {"source": "n1", "target": "n4", "label": "classified_as"},
            }
        }

kb_service = KnowledgeBaseService.get_instance()
