# 任务计划：Agent 与 Agno 生态系统验证与开发

## 第一阶段：状态验证 (已完成)
- [x] 验证第二阶段依赖 (yfinance, openbb 等) <!-- id: 1 -->
- [x] 验证第三阶段依赖 (duckdb, pandas 等) <!-- id: 2 -->
- [x] 验证第四阶段依赖 (github, docker, media tools) <!-- id: 3 -->
- [x] 检查 `app/services/agent/tools/` 现有工具实现 <!-- id: 4 -->
- [x] 检查 `app/services/agent/manager.py` 工具注册逻辑 <!-- id: 5 -->
- [x] 检查前端 `AgentEditorDrawer.vue` 工具配置界面 <!-- id: 6 -->
- [x] 检查现有的 "Financial", "Data", "Media" 工具集成代码 <!-- id: 7 -->

## 第二阶段：缺口分析与优化 (已完成)
- [x] 分析缺失的后端工具包装器 <!-- id: 8 -->
- [x] 分析缺失的前端配置字段 (API Key, 文件上传) <!-- id: 9 -->
- [x] 识别代码结构优化点 (工具工厂模式) <!-- id: 10 -->
- [x] 识别安全风险 (如 SQL 注入风险) <!-- id: 11 -->

## 第三阶段：文档生成 (已完成)
- [x] 生成状态报告 `docs/Agent/status_report_20250312.md` <!-- id: 12 -->
- [x] 创建优化方案 `docs/Agent/optimization_plan_v2.md` <!-- id: 13 -->
- [x] 更新 `docs/Agent/task.md` <!-- id: 14 -->

## 第四阶段：核心功能实现 (已完成)
- [x] 安装核心依赖 (yfinance, duckdb, financial-datasets, arxiv, wikipedia 等) <!-- id: 15 -->
- [x] **后端架构升级**：
    - [x] 更新 `discovery.py` 支持元数据提取 (`_label`, `_description`, `config_schema`) 与多工具扫描。
    - [x] 新增 API 接口：`GET /api/v1/tools/available` 用于动态获取工具列表。
    - [x] 更新 `manager.py` 支持基于字典配置的动态工具实例化。
- [x] **工具模块实现**：
    - [x] 金融类：`financial.py` (YFinance, OpenBB)。
    - [x] 数据类：`data.py` (DuckDB, Pandas), `db_tools.py` (SQLTools)。
    - [x] Web 类：`web_tools.py` (Website, Arxiv, Wikipedia)。
    - [x] 文件类：`file_tools.py` (File, PDF, JSON)。
    - [x] 实用类：`calculator.py`。
- [x] **前端重构**：
    - [x] 重构 `AgentEditorDrawer.vue`，移除硬编码工具列表，改为从后端 API 动态加载。
    - [x] 实现基于 JSON Schema 的动态配置表单 (支持 API Key, 文件路径等输入)。

## 第五阶段：UI/UX 优化与功能增强 (已完成)
- [x] **界面优化**：
    - [x] 工具箱与知识库列表改为**卡片网格布局** (2列)，节省空间。
    - [x] 统一卡片样式（边框、阴影、悬停效果），去除多余图标。
    - [x] 实现工具箱**分类筛选**功能 (支持中文分类映射)。
- [x] **本地化**：
    - [x] 后端工具元数据 (`_label`, `_description`) 全面中文化。
    - [x] 前端分类标签中文化 (如 "search" -> "网络搜索")。
- [x] **调试监控**：
    - [x] 后端 `manager.py` 支持 `show_tool_calls` 参数。
    - [x] 前端增加“监控”开关，开启后可在终端实时查看 Agent 思考与调用过程。
- [x] **问题修复**：
    - [x] 修复删除 `duckduckgo.py` 导致的 `ModuleNotFoundError`。

## 变更总结

### 新增接口
- `GET /api/v1/tools/available`: 返回所有可用工具的元数据列表（包含名称、中文标签、描述、分类、配置 Schema）。

### 逻辑变更
1.  **工具发现机制 (`discovery.py`)**:
    - 支持扫描单个文件中的多个 `Toolkit` 子类。
    - 优先使用 `_name` 属性作为工具唯一标识，回退到类名转换。
    - 自动提取 `pydantic` 配置模型生成 JSON Schema。
2.  **Agent 初始化 (`manager.py`)**:
    - 支持处理 `{name: "tool_name", config: {...}}` 格式的工具配置。
    - 读取 `model_config.show_tool_calls` 并传递给 Agno 框架以启用调试输出。
3.  **前端交互 (`AgentEditorDrawer.vue`)**:
    - 初始化时调用 API 获取工具列表。
    - 根据 `config_schema` 动态渲染配置表单。
    - 实现前端分类映射逻辑，确保展示中文分类。

### 待解决问题 / 后续建议
- [ ] **OpenBB 深度集成**: 目前仅为占位符，需要根据具体业务需求实现具体的 OpenBB 功能。
- [ ] **沙箱环境增强**: 目前 E2B 沙箱基础功能已通，可考虑增加文件上传/下载的前端交互。
- [ ] **MCP 市场**: 目前仅支持手动配置 MCP，可考虑接入 MCP 注册中心。
