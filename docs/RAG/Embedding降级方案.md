# RAG Embedding 失败/欠费降级方案

## 背景

在知识库检索与问答链路中，Embedding 是向量检索与语义检索的关键依赖。当对接的 Embedding 服务端发生不可用（例如阿里云 Model Studio/DashScope 账号欠费导致 400 Arrearage）时，会出现：

- Query embedding 预计算失败，向量检索不可用或质量急剧下降
- QA 可能直接报错或返回空结果

本方案目标是在 Embedding 不可用的情况下，让系统“不中断”，并尽量提供可用但降级的回答能力与可观测性。

## 目标

- Embedding 调用失败时，链路不中断（不抛出导致服务失败的异常）
- QA 在文档范围（doc scope）至少可以回退到“内容扫描检索（非向量）”
- 输出足够的日志与状态，便于定位账号欠费、鉴权失败、服务不可用等根因

## 适用范围

- RAG/QA 主链路（LightRAG 引擎 + QAService）
- Embedding 提供方通过 OpenAI SDK 的 embeddings 接口对接（包括阿里云 OpenAI 兼容模式）

配置来源说明：

- LLM/Embedding 的 `api_key/base_url/model_id` 主要由数据库表 `llm_models` 的激活模型提供
- LightRAG 初始化阶段会写入 `OPENAI_API_KEY/OPENAI_BASE_URL` 到进程环境变量，影响依赖环境变量的下游组件

## 降级策略总览

当 Embedding 不可用时，采用多层降级（从底层到上层）：

1. **Embedding 层降级（强制不中断）**
   - Embedding 请求失败：返回“零向量”（shape 对齐为 `(len(texts), embed_dim)`）
   - 记录最近一次 Embedding 错误与时间戳，便于上层/监控读取
2. **检索层降级（doc scope 优先保证可用）**
   - 文档专用向量检索无命中或不可用：改用“内容扫描检索”（substring + 简单覆盖度评分）召回片段
   - 内容扫描仍无命中：回退到读取文档前文（前 8000 字）作为上下文
3. **生成层降级（最终保底）**
   - LLM 生成失败：切换到 local 模式再尝试
   - 若仍无效：输出“相关文档片段整理”或“未检索到有效答案”

## 实现细节（代码落点）

### 1) Embedding 层：失败返回零向量 + 状态记录

落点：`backend/app/services/rag/retrieval/engines/lightrag.py`

- 在 `embedding_func()` 内部捕获 `embeddings.create(...)` 异常，返回零向量，并记录：
  - `_embedding_last_error`
  - `_embedding_last_error_at`
  - `_embedding_last_ok_at`
- 同时对 `lightrag.llm.openai.openai_embed` 的 patch 也做同样降级（覆盖 LightRAG 内部可能的同步 embedding 调用路径）
- 提供两个查询接口：
  - `get_last_embedding_error()`
  - `embedding_recently_failed(within_seconds=300)`

### 2) QA（流式）doc scope：向量检索空结果时做内容扫描

落点：`backend/app/services/rag/generation/qa.py`

- 新增 `_content_search()`：
  - 读取全文 → chunk → substring 命中 + 字符覆盖度加分 → top_k 片段
  - 该检索不依赖 embedding/向量库
- 在 `qa_stream()` 的 doc scope 中，当 `search_doc_chunks(...)` 返回空时：
  1) 先 `_content_search()`
  2) 仍无命中再读文档前文（前 8000 字）补上下文

### 3) QA（非流式）doc scope：mix 调用异常/无效时做内容扫描兜底

落点：`backend/app/services/rag/generation/qa.py`

- `query_async(mode="mix")` 调用增加异常捕获
- 若生成结果无效（空、敏感词屏蔽等），在进入“向量片段补救”前，优先尝试：
  - doc scope：读取当前文档 → `_content_search()` → 组装“片段整理”作为 answer，并填充 `sources`（source=content_scan）

## 行为说明与权衡

### 零向量降级的影响

- 好处：避免链路因为 embedding 接口异常直接失败；LightRAG 内部依赖 embedding 的调用可以继续执行
- 代价：向量相似度检索会显著退化（大量零向量会让结果变得随机或无区分度）
- 适用：短期保可用、保障服务不中断；长期仍应修复根因（充值/恢复权限/切换 embedding 提供方）

### 内容扫描降级的影响

- 好处：完全不依赖 embedding，可在欠费/鉴权失败时继续提供“可解释”的片段召回
- 代价：召回质量依赖关键词与字符覆盖度，语义能力弱；对大文件读取与分块可能增加 CPU/IO 消耗
- 适用：doc scope（用户指定文档）最有效；global scope 若要引入全文检索需额外索引能力（未在本次方案中实现）

## 可观测性与排障建议

- 当出现 `400 Arrearage / Access denied` 等错误：
  - 首先检查 embedding 提供方账号状态（欠费/额度/鉴权）
  - 检查 DB 中激活的 embedding 模型配置（`llm_models`）是否正确（api_key/base_url/model_id）
- 建议在运行侧增加告警规则：
  - 最近 5 分钟 embedding 失败次数 > 阈值
  - `embedding_recently_failed()` 为 true 且持续超过阈值时间

## 验证步骤（最小）

- 人工制造 Embedding 不可用（例如使用无效 key 或断网）后：
  1) doc scope 提问应仍有输出，且过程提示中出现“内容扫描检索”相关提示
  2) 若文档中存在明显关键词，回答应输出“片段整理”而不是直接报错
  3) 全链路不应因为 embedding 异常直接返回 500

