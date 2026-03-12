# 调查发现

## 代码库验证

### 依赖项
- **缺失:** `yfinance`, `openbb`, `duckdb`, `financial-datasets`。
- **已安装:** `pandas`。
- **第四阶段:** 尚未检查，但可能缺失 `github`, `docker`, `openai` (用于 DALL-E) 等。

### 后端实现
- **工具封装:**
    - `duckduckgo.py`: 已实现。
    - `sandbox_tools.py`: 已实现 (E2B)。
    - `mcp_tool.py`: 已实现。
    - `factory.py`: 已实现。
    - `runner.py`: 已实现。
- **工具注册 (`app/services/agent/manager.py`):**
    - 从 `app/services/tools/` 动态发现。
    - 手动注入 `OpenClaw`, `Sandbox`, `MCP`, `DuckDuckGo`, `KnowledgeBase`, `N8N`, `FileSkills`。
    - **缺失:** `Financial` (金融), `Data` (数据), `Dev` (开发), `Media` (媒体) 工具的逻辑。

### 前端实现
- **AgentEditorDrawer.vue**:
    - `defaultTools` 仅包含 `DuckDuckGo`, `Calculator`, `N8N`。
    - 缺失 `Financial`, `Data`, `Dev`, `Media` 工具的 UI。
    - 没有针对 API 密钥（除通用智能体配置外）或数据文件上传的配置字段。
    - 工具选择仅限于默认工具的复选框或动态 MCP/技能添加。

## 差距与优化

### 差距
1.  **缺失依赖项:** `yfinance`, `openbb`, `duckdb`, `financial-datasets`。
2.  **缺失后端工具封装:**
    - `app/services/agent/tools/financial.py`
    - `app/services/agent/tools/data.py`
    - `app/services/agent/tools/dev.py` (GitHub, Docker)
    - `app/services/agent/tools/media.py` (DALL-E 等)
3.  **缺失前端 UI:**
    - `AgentEditorDrawer.vue` 中新工具的复选框。
    - API 密钥（例如 GitHub Token, OpenBB Key）和文件上传（用于 Pandas/DuckDB）的配置输入框。

### 优化
1.  **动态工具加载:** 不要在前端硬编码 `defaultTools`，而是从后端端点 (`/api/v1/tools/available`) 获取可用工具。这确保前端和后端始终同步。
2.  **统一工具配置:** 创建一种标准化方式来定义工具配置模式（使用 JSON Schema），以便前端可以动态生成任何工具的表单（类似于处理 MCP 参数的方式，但更用户友好）。
3.  **安全性:** 确保 SQL/Shell 工具经过严格沙盒化（E2B 已部分完成，但本地 DuckDB/Pandas 需要小心）。
