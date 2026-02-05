# Taichi 知识图谱系统架构与实现详解

> **文档版本**：v2.2  
> **更新时间**：2026-02-03  
> **适用场景**：智能问答、推荐系统、企业知识管理、风控分析、科研辅助  
> **核心特性**：多源异构数据融合、混合检索 (Hybrid RAG)、双路图谱构建 (LightRAG + Neo4j)、亿级规模高性能

---

## 目录

1. [一、多源数据抽取与解析 (Data Ingestion)](#一多源数据抽取与解析-data-ingestion)
2. [二、数据融合与治理 (Data Fusion)](#二数据融合与治理-data-fusion)
3. [三、高性能图谱构建 (High Performance Construction)](#三高性能图谱构建-high-performance-construction)
4. [四、核心代码实现深度解析 (Core Implementation)](#四核心代码实现深度解析-core-implementation)
5. [五、后端智能应用 (Backend Intelligence)](#五后端智能应用-backend-intelligence)
6. [六、前端可视化交互 (Visualization)](#六前端可视化交互-visualization)
7. [七、关键技术栈 (Tech Stack)](#七关键技术栈-tech-stack)

---

## 一、多源数据抽取与解析 (Data Ingestion)

系统支持结构化、半结构化及非结构化数据的全量接入，针对不同数据类型采用差异化的抽取策略。

### 1.1 结构化数据 (Structured Data)
*   **来源**：关系型数据库 (MySQL, PostgreSQL)、数仓 (Hive, ClickHouse)
*   **策略**：
    *   **Schema 映射**：将表名映射为实体类型，主键映射为实体ID，外键映射为关系。
    *   **ETL 转换**：利用 SQL 或 Python 脚本进行字段清洗与标准化。
*   **示例**：
    *   `Users` 表 -> `User` 实体
    *   `Orders` 表 -> `Order` 实体
    *   `user_id` 外键 -> `(User)-[PLACED]->(Order)` 关系

### 1.2 外部接口数据 (API Data)
*   **来源**：REST API, GraphQL, 第三方数据平台 (如企查查, Bloomberg)
*   **策略**：
    *   **适配器模式**：针对不同 API 编写适配器，标准化返回的 JSON/XML 数据。
    *   **Web Search**：集成 Tavily/Aliyun 搜索 API 获取实时网络信息。
*   **代码参考**：[search_service.py](backend/app/services/search_agent/search_service.py)

### 1.3 非结构化数据 (Unstructured Data)

#### 文本与文档
*   **格式**：PDF, DOCX, TXT
*   **实现**：多级回退解析 (PyMuPDF -> pdfplumber -> OCR)。
*   **代码参考**：[document_parser.py](backend/app/services/document_parser.py)

#### 网站内容 (HTML)
*   **场景**：新闻抓取、政策公告、竞品分析
*   **策略**：基于 `aiohttp` 和 `BeautifulSoup` 的异步爬虫，自动发现搜索表单与列表页。
*   **代码参考**：[debug_crawler.py](debug_crawler.py)

#### 音视频媒体 (Audio/Video)
*   **场景**：会议记录、客服录音、视频教程
*   **策略**：利用 ASR (自动语音识别) 提取文本，结合时序信息切分内容。
*   **实现**：集成阿里云 NLS 服务，支持长语音异步转写。
*   **代码参考**：[aliyun_asr_service.py](backend/app/services/aliyun_asr_service.py)

#### 邮件与通信 (Email)
*   **场景**：社交网络分析、犯罪调查、企业沟通挖掘
*   **策略**：
    *   解析 Header 提取 `From`, `To`, `Cc` 构建通信关系网。
    *   解析 Body 提取正文实体与事件。
    *   分析时间戳构建时序交互图。

#### 图片与多模态 (Image)
*   **场景**：文档插图、扫描件、实景照片
*   **策略**：OCR 文字提取 + 图像 Captioning (生成描述) -> 实体抽取。

---

## 二、数据融合与治理 (Data Fusion)

多源数据接入后，必须解决多义词、同义词、数据冲突等问题，确保图谱质量。

### 2.1 实体对齐 (Entity Alignment)
*   **目标**：将不同来源的 "Aliyun", "阿里云", "Alibaba Cloud" 统一为同一实体。
*   **技术**：
    *   **规则匹配**：基于同义词词典、正则表达式。
    *   **相似度计算**：计算实体名称的 Jaro-Winkler 距离或 Embedding 余弦相似度。
    *   **图结构对齐**：基于邻居节点的相似性进行对齐 (Graph Matching)。

### 2.2 冲突消解 (Conflict Resolution)
*   **场景**：不同源对同一属性描述不一致 (如某公司成立时间)。
*   **策略**：
    *   **置信度优先**：优先采用官方/权威数据源 (如数据库 > 网页)。
    *   **时间优先**：采用最新的数据更新。
    *   **投票机制**：多数源一致的值胜出。

### 2.3 时效性管理 (Timeliness)
*   **事实有效性**：为关系和属性添加 `valid_from` 和 `valid_to` 时间窗口。
*   **版本控制**：图谱支持快照，可回溯历史状态。

---

## 三、高性能图谱构建 (High Performance Construction)

针对百万至亿级实体规模，系统设计了高性能的存储与写入方案。

### 3.1 Neo4j 优化策略
*   **约束与索引 (Constraints & Indexes)**：
    *   在写入前必须创建唯一性约束 (`CREATE CONSTRAINT ON (n:Entity) ASSERT n.id IS UNIQUE`)，防止重复并加速 Merge。
    *   为常用查询属性 (name, type, created_at) 创建索引。
*   **批量导入 (Batch Import)**：
    *   使用 `UNWIND` 语法进行批量写入，减少网络开销与事务提交次数。
    *   推荐批次大小：1000 - 5000 条/次。
*   **代码参考**：[graph_service.py](backend/app/services/graph_service.py)

### 3.2 增量同步 (Incremental Sync)
*   **CDC (Change Data Capture)**：监听数据库 Binlog，实时捕获数据变更同步至图谱。
*   **定期增量**：记录上次同步的时间戳，仅处理更新时间 > 上次同步时间的数据。

---

## 四、核心代码实现深度解析 (Core Implementation)

本节重点解析非结构化文本数据在解析、分块、向量化和图谱构建环节的核心代码逻辑。

### 4.1 多级回退解析器 (Parsing)

**核心挑战**：不同来源的 PDF 质量差异大（矢量 vs 扫描件），单一库无法满足所有需求。

**解决方案**：级联式解析策略 (Cascade Strategy)。

**代码位置**：`backend/app/services/document_parser.py`

```python
def parse_local_file(file_path: str) -> str:
    # 策略 1: PyMuPDF (fitz) - 速度最快，支持元数据提取
    try:
        import fitz
        doc = fitz.open(file_path)
        # ... 提取文本 ...
        return text
    except:
        pass
        
    # 策略 2: pdfplumber - 擅长复杂布局（如多栏、表格）
    if not parsed:
        import pdfplumber
        # ...
        
    # 策略 3: pypdf - 纯Python实现，兼容性兜底
    if not parsed:
        import pypdf
        # ...

    # 策略 4: OCR (Tesseract) - 针对纯图片型 PDF
    if settings.OCR_ENABLED and not text.strip():
        # 将 PDF 页面渲染为图像，再进行 OCR 识别
        # ...
```

### 4.2 智能语义分块 (Semantic Chunking)

**核心挑战**：如何切分文本以保持语义完整性，避免截断关键信息。

**解决方案**：基于 Token 数量的滑动窗口分块。

**配置代码**：`backend/app/services/lightrag_service.py`

```python
self.rag = LightRAG(
    # ...
    chunk_token_size=1200,          # 块大小：约 1200 tokens (适配中文语境)
    chunk_overlap_token_size=100,   # 重叠大小：100 tokens (保持上下文连贯)
    # ...
)
```

### 4.3 动态向量化适配 (Dynamic Embedding)

**核心挑战**：不同 Embedding 模型（OpenAI, Aliyun, HuggingFace）输出维度不同（1024/1536/2048/3072），需要兼容同一向量库。

**解决方案**：Monkey Patch + 动态维度截断/补齐。

**代码位置**：`backend/app/services/lightrag_service.py`

```python
# 1. Monkey Patch: 覆盖 LightRAG 默认的 OpenAI 实现
def _patched_openai_embed(texts, model, api_key=None, base_url=None, embedding_dim=None):
    # 调用兼容 OpenAI 协议的接口 (支持 DashScope, DeepSeek 等)
    resp = client.embeddings.create(model=model, input=texts)
    emb = [d.embedding for d in resp.data]
    return np.array(emb)

# 2. 动态维度处理逻辑
async def embedding_func(texts: list[str]) -> np.ndarray:
    # ... 获取原始向量 ...
    actual_dim = out.shape[1]
    
    if actual_dim > embed_dim:
        # 维度过大 -> 截断 (通常前序维度包含主要语义信息)
        out = out[:, :embed_dim]
    elif actual_dim < embed_dim:
        # 维度过小 -> 补零 (Zero Padding)
        pad = np.zeros((out.shape[0], embed_dim - actual_dim), dtype=float)
        out = np.concatenate([out, pad], axis=1)
        
    return out
```

### 4.4 图谱构建与实体提取 (Prompt Engineering)

**核心挑战**：通用 LLM 提取的实体往往过于零散，且不支持中文优化。

**解决方案**：定制化 System Prompt，强制结构化输出与中文规范。

**代码位置**：`backend/app/services/lightrag_service.py`

```python
# 注入自定义 Prompt
_lp.PROMPTS["entity_extraction_system_prompt"] += """
注意：
1. **中文强制**：请务必使用简体中文输出所有实体名称、类型和描述。
2. **文档实体化**：始终将“源文档/文件”提取为一个独立的实体，并将文中提取的所有其他实体与该“文档”实体建立联系（如“提及于”）。
3. **专业术语**：对于必须保留英文的专有名词（如 Transformer, LLM），保持标准大小写，严禁全小写。
"""
```

---

## 五、后端智能应用 (Backend Intelligence)

### 5.1 高级检索与问答
1.  **GraphRAG (图谱增强生成)**：
    *   利用图谱的多跳关系 (Multi-hop) 补充上下文，回答 "A 对 B 有什么影响" 类问题。
2.  **混合检索 (Hybrid Search)**：
    *   **架构**：`BM25 (关键词)` + `Vector (语义)` + `Graph (结构)` -> `Rerank (重排序)` -> `LLM`。
    *   **优势**：兼顾精确匹配与语义理解，解决长尾问题。
    *   **代码参考**：[qa_service.py](backend/app/services/qa_service.py)

### 5.2 深度图分析
1.  **时序查询 (Temporal Query)**：
    *   "查询 2023 年至 2024 年间该公司的股权变更路径"。
    *   基于边属性的时间窗口过滤。
2.  **路径查询 (Pathfinding)**：
    *   最短路径 (ShortestPath)：寻找两个实体间的最短关联。
    *   全路径 (AllSimplePaths)：发现所有可能的关联链路 (用于风控关联排查)。
3.  **聚类分析 (Clustering)**：
    *   Louvain / Label Propagation 算法，发现社区结构 (Community Detection)。
4.  **异常监测 (Anomaly Detection)**：
    *   基于 PageRank 或中心度算法，识别关键节点或异常孤立点。
5.  **图嵌入 (Graph Embedding)**：
    *   Node2Vec / GraphSAGE：将节点转为向量，用于下游分类或链接预测任务。

---

## 六、前端可视化交互 (Visualization)

基于 `v-network-graph` 实现高度可交互的知识图谱前端。

### 6.1 实体卡片 (Entity Card)
点击节点展示详情面板，包含：
*   **基础信息**：名称、类型、全局唯一ID。
*   **属性列表**：键值对展示 (Key-Value)，支持折叠/展开。
*   **描述摘要**：LLM 生成的实体摘要。
*   **关联溯源**：
    *   **来源文档**：链接到原始 PDF/Word 文件。
    *   **原文片段 (Chunks)**：展示提取该实体的具体文本段落。
    *   **置信度**：数据来源的可信评分。

### 6.2 探索与交互
*   **多跳探索**：双击节点展开其邻居节点，动态加载子图。
*   **路径高亮**：点击两个节点，自动高亮它们之间的最短路径。
*   **布局切换**：力导向 (Force)、网格 (Grid)、环形 (Circle)。

### 6.3 智能筛选
*   **按类型**：只看 "人物" 或 "公司"。
*   **按关系**：只看 "投资" 或 "任职" 关系。
*   **按时间**：时间轴拖动，过滤特定时间段的关系。
*   **按属性**：筛选 "注册资本 > 1000万" 的实体。

**代码参考**：[GraphViewer.vue](frontend/src/components/common/GraphViewer.vue)

---

## 七、关键技术栈 (Tech Stack)

| 模块 | 技术选型 | 说明 |
|------|----------|------|
| **数据源接入** | Python (aiohttp, PyMuPDF), Aliyun SDK | 多模态解析与爬虫 |
| **NLP & AI** | LightRAG, OpenAI/DashScope | 实体抽取、向量化、摘要生成 |
| **图数据库** | **Neo4j** (Enterprise/Community) | 核心存储、Cypher 查询、图算法 |
| **向量数据库** | NanoVectorDB / Milvus | 向量索引 |
| **后端服务** | FastAPI | 高性能异步 API |
| **前端可视化** | **v-network-graph**, D3.js | 交互式图谱渲染 |
| **任务调度** | Celery / N8n | 定时爬虫、增量同步任务 |
