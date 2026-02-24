# 实施检查清单 (Agno 集成)

## 1. 后端核心 (Agno 智能体)
- [ ] **依赖**: `backend/requirements.txt` 已更新，包含 `agno`, `pydantic`。
- [ ] **智能体管理器**: `backend/app/services/agent/manager.py` 中的 `AgentManager` 支持创建 `agno.agent.Agent`。
- [ ] **规划智能体**: 已实现并返回结构化的任务计划 (`Task` 模型)。
- [ ] **执行智能体**: 成功接收任务并使用工具执行。
- [ ] **任务持久化**: 任务以正确的状态 (`pending`, `in_progress` 等) 存储在数据库中。
- [ ] **WebSocket API**: `/api/v1/ws/agent/{session_id}` 处理双向流式传输 (Token + 工具调用)。

## 2. 沙箱集成 (工具包)
- [ ] **沙箱服务**: `TaskSpace` 正确处理资源限制 (CPU/内存)。
- [ ] **工具包类**: `SandboxToolkit` 已在 `backend/app/services/agent/tools/sandbox_tool.py` 中实现并注册。
- [ ] **执行**: 智能体可以执行 Python 代码: `print("hello")` -> 返回 `hello`。
- [ ] **文件**: 智能体可以在沙箱中 `list_files` (列出文件), `read_file` (读取文件), `write_file` (写入文件)。
- [ ] **安全性**: 沙箱容器无法访问受限的网络资源。
- [ ] **冷启动**: 容器启动时间 < 2s (实测)。

## 3. 知识库 (混合 RAG)
- [ ] **RAG 引擎**: 已实现结合向量 + 关键词搜索的 `HybridRetriever`。
- [ ] **重排序**: 集成 `CrossEncoder` 并提高了检索精度。
- [ ] **知识库类**: `CustomKnowledgeBase` 实现了 Agno 的 `KnowledgeBase` 接口。
- [ ] **文档摄取**: PDF/Markdown 上传已被异步处理并建立索引。
- [ ] **检索**: 智能体可以从知识库中检索相关信息并提供引用。

## 4. 前端 (Vue 3)
- [ ] **聊天 UI**: 显示流式 Token、工具调用和可折叠的思维过程。
- [ ] **任务树**: 可视化任务依赖关系和实时状态更新。
- [ ] **代码编辑器**: Monaco Editor 正常工作，支持语法高亮和自动补全。
- [ ] **终端**: Xterm.js 流式传输来自沙箱的标准输出/错误。
- [ ] **文件预览**: 生成的产物 (图像、表格) 能够正确渲染。
- [ ] **知识库仪表盘**: 支持文件上传、管理和搜索测试。

## 5. 系统质量
- [ ] **性能**: 后端 API P99 < 500ms。
- [ ] **可靠性**: 对失败的工具调用/超时进行错误处理。
- [ ] **监控**: 采集智能体执行、沙箱使用和知识库检索的指标。
- [ ] **测试**: 单元测试覆盖核心逻辑 (覆盖率 >80%)。
- [ ] **文档**: `DEPLOY.md`, `API.md`, `OPS.md` 已完成。
