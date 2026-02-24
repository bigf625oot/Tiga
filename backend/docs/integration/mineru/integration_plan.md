# MinerU 集成与迁移技术方案

## 1. 功能对比分析

### 1.1 解析能力对比

| 维度 | 当前项目 (Tiga RAG) | MinerU (Magic-PDF) | 差异总结 |
| :--- | :--- | :--- | :--- |
| **支持文件** | PDF, DOCX, TXT | PDF (主要), PPT/PPTX, DOC/DOCX | MinerU 专注 PDF 深度解析，当前项目覆盖面更广但深度浅。 |
| **PDF 解析原理** | 基于规则提取 (`PyMuPDF`/`pdfplumber`) + 基础 OCR (`Tesseract`) | 基于视觉模型 (Layout Analysis) + 深度学习 OCR (`PP-OCR`) + 公式/表格识别模型 | **MinerU 遥遥领先**，能理解文档视觉结构。 |
| **复杂版面** | **弱**。双栏文档可能会跨栏读取导致语序混乱；页眉页脚混入正文。 | **强**。自动识别阅读顺序，剔除页眉页脚、页码，还原多栏布局。 | 复杂文档（如论文、研报）解析效果差距巨大。 |
| **表格处理** | **弱**。仅提取文本，丢失结构，或通过 `pdfplumber` 勉强提取。 | **强**。自动识别表格边界，转换为 HTML/Markdown 表格，支持跨页合并。 | MinerU 能保留表格语义。 |
| **公式处理** | **不支持**。通常解析为乱码或丢失。 | **强**。使用 `UniMERNet` 将公式转换为 LaTeX 格式。 | 学术文献解析的关键差异。 |
| **图片提取** | 支持（提取为文件），但缺乏上下文关联。 | 支持，且能提取图片标题（Caption）并尝试关联正文位置。 | MinerU 的多模态对齐能力更强。 |
| **处理速度** | **极快** (非 OCR 模式)。纯 CPU 毫秒级/页。 | **较慢**。需要模型推理，CPU 模式下约几秒/页，建议使用 GPU。 | 速度与精度的权衡。 |

### 1.2 分块 (Chunking) 策略对比

*   **当前项目**：
    *   **策略**：侧重于“文本流”切分。
    *   **实现**：先按段落（`\n\n`）切分，再按句子切分，最后合并成固定长度（Token/字符数）的块。
    *   **缺陷**：由于解析阶段丢失了结构信息（如“这是一级标题”），导致切分时很难按章节语义精准切开，容易出现“标题与正文分离”或“跨章节合并”的问题。

*   **MinerU (集成后)**：
    *   **策略**：侧重于“结构化”切分。
    *   **优势**：MinerU 输出的是**高质量的 Markdown**。这意味着我们可以利用 Markdown 的标题层级（`#`, `##`）进行**结构化分块 (MarkdownHeaderSplitter)**。
    *   **效果**：可以实现“一个章节一个 Chunk”或“基于标题层级的递归切分”，语义完整性远超纯文本切分。

## 2. 技术架构差异

| 特性 | 当前项目架构 | MinerU 架构 |
| :--- | :--- | :--- |
| **底层依赖** | `fitz` (PyMuPDF), `pdfplumber`, `python-docx`, `pytesseract` | `PyTorch`, `Detectron2` (旧版) / `YOLO`, `PaddleOCR` (PP-OCR), `UniMERNet` |
| **硬件要求** | 低。普通 CPU 即可运行，内存占用小。 | 高。推荐 **NVIDIA GPU (CUDA)** 或 NPU，显存建议 8GB+。CPU 运行慢且占用高。 |
| **部署难度** | 简单。`pip install` 即可，依赖少。 | 复杂。需配置 CUDA 环境，下载多个模型权重文件（Layout, OCR, Formula 等）。 |
| **扩展性** | 代码逻辑简单，易于修改规则。 | 模块化设计（Pipeline），可替换 OCR 或 Layout 模型，但技术门槛高。 |
| **错误处理** | 简单的 Try-Catch 降级机制（fitz -> pdfplumber -> ocr）。 | 复杂的模型推理流程，需处理 CUDA OOM、模型加载失败等异常。 |

## 3. MinerU 集成方案设计

### 3.1 环境配置要求

*   **OS**: Linux (推荐) / Windows (需处理路径和编码问题) / macOS
*   **Python**: >= 3.10
*   **GPU**: 建议 NVIDIA 显卡，显存 >= 8GB (4GB 可运行但受限)。无 GPU 则需高性能 CPU。
*   **依赖安装**:
    ```bash
    # 基础依赖
    pip install magic-pdf[full] 
    # 检测并安装对应版本的 torch (需根据 CUDA 版本调整)
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
    ```
*   **模型下载**:
    需从 HuggingFace/ModelScope 下载权重文件并配置 `magic-pdf.json` 指向该目录。

### 3.2 代码集成步骤

建议创建一个新的解析器类 `MinerUParser` 继承自基类，作为可选的高级解析器。

**A. 配置文件 (`magic-pdf.json`)**:
在项目根目录或 `config` 目录生成配置文件，指定模型路径。

**B. 调用代码示例**:

```python
# backend/app/services/rag/parsers/mineru_parser.py

from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import Pipedata
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
import os
import logging

logger = logging.getLogger(__name__)

class MinerUParser:
    def __init__(self):
        # 初始化配置，检查模型文件是否存在
        pass

    async def parse(self, file_path: str):
        try:
            # 1. 准备数据
            image_writer = FileBasedDataWriter(os.path.dirname(file_path))
            image_dir = str(os.path.basename(file_path)).split('.')[0] + "_images"
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 2. 模型推理 (Layout Analysis + OCR + Formula)
            # 注意：此过程较慢，建议放入独立线程或 Celery 任务中
            ds = Pipedata(file_content)
            
            # 自动选择处理模式 (txt/ocr)
            model_output = doc_analyze(ds)
            
            # 3. 生成 Markdown
            # MinerU 提供了直接生成 markdown 的接口
            markdown_content = model_output[0]['md_content']
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"MinerU parse failed: {e}")
            raise
```

### 3.3 数据格式转换

*   **映射关系**:
    *   MinerU Output (`.md`) -> `Document.page_content`
    *   MinerU Images -> 上传至对象存储 -> 替换 Markdown 中的图片链接
    *   MinerU Tables (HTML) -> 保留 HTML 或转为 Markdown Table -> `Document.page_content`

### 3.4 性能优化建议

1.  **异步队列**: MinerU 解析极耗时（单页可能 5-10秒），**必须**使用 Celery/Redis Queue 进行异步处理，不可在 API 请求中同步等待。
2.  **GPU 批处理**: 如果有多张显卡，可启动多个 Worker 并绑定不同 GPU。
3.  **缓存**: 对解析结果（Markdown）进行持久化缓存（基于文件 Hash），避免重复解析。
4.  **降级策略**: 检测到文件页数过多（>50页）或系统负载过高时，自动降级回 `PyMuPDF` 快速解析。

## 4. 迁移实施计划

### 阶段一：POC 验证与环境准备 (1周)
1.  **环境搭建**: 在开发/测试服务器配置 CUDA 环境，下载 MinerU 模型。
2.  **原型开发**: 编写脚本跑通 `pdf -> markdown` 的流程。
3.  **效果评估**: 选取 10 个典型文档（纯文本、图文混排、表格多、公式多）进行对比测试。

### 阶段二：集成开发 (2周)
1.  **封装 Service**: 实现 `MinerUParser` 类。
2.  **异步化改造**: 确保文档解析流程支持异步任务（如果当前是同步的，需引入 Task Queue）。
3.  **配置开关**: 在系统设置中添加 `USE_MINERU_PARSER` 开关。

### 阶段三：灰度发布与优化 (1-2周)
1.  **数据迁移**: 老数据暂不迁移，新上传文档优先使用 MinerU。
2.  **监控**: 重点监控 GPU 显存使用率和解析失败率。
3.  **回滚机制**: 如果 MinerU 报错，捕获异常并自动 fallback 到 `PyMuPDF`。

## 5. 交付标准

### 5.1 集成验证报告
*   **准确率**: 随机抽取 50 页复杂文档，人工核对 Markdown 结构、表格内容、公式显示的正确性。目标准确率 > 90%。
*   **完整性**: 图片、表格是否丢失。

### 5.2 性能基准
*   **速度**: 单页 PDF (A4, 混排) 解析耗时 < 5秒 (GPU 4090) / < 15秒 (CPU)。
*   **资源**: 显存占用稳定在 8GB 以内（单并发）。

### 5.3 交付物
1.  **部署脚本**: 包含 CUDA 驱动检查、Python 依赖安装、模型自动下载脚本。
2.  **操作手册**: 说明如何切换解析引擎，如何更新模型。
3.  **维护指南**: 常见报错（如 CUDA OOM）的处理方案。
