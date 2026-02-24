# Agno 框架 E2B 沙箱服务集成分析报告

## 1. 概述
本报告详细分析了 Agno 框架中关于 E2B 沙箱服务的集成情况，基于对 `shell.py`, `e2b.py`, `sandbox_tools.py` 及 `manager.py` 的代码审计。

**结论**: Agno 框架**已集成** E2B 沙箱服务，但属于**条件触发集成**，非全局默认开启。

## 2. 集成状态分析

| 组件 | 文件路径 | 集成状态 | 说明 |
| :--- | :--- | :--- | :--- |
| **ShellTools** | `app/services/agent/tools/shell.py` | 🔴 **未集成** | 本地 Shell 执行工具，出于安全考虑，默认未在 `manager.py` 中启用。 |
| **E2BTools** | `app/services/agent/tools/e2b.py` | 🔴 **未集成** | 全功能的 E2B 工具包，但在 Agent 创建流程中未被引用。 |
| **SandboxTools** | `app/services/agent/tools/sandbox_tools.py` | 🟢 **条件集成** | 当前实际使用的 E2B 适配层，仅当 Agent 配置了 Sandbox 技能时注入。 |

## 3. 详细代码证据

### 3.1 核心集成逻辑 (`manager.py`)
Agno Agent 的创建工厂 `AgentManager.create_agno_agent` 中包含以下逻辑：

- **文件**: `backend/app/services/agent/manager.py`
- **行号**: 206-241 (预估)

```python
# 1. 检查启用条件：skills_config 中的 'sandbox' 字段或 legacy 工具名
is_sandbox_enabled = skills_config.get("sandbox", {}).get("enabled")

if not is_sandbox_enabled and isinstance(tools_config, list):
    for t in tools_config:
        if isinstance(t, str) and t.startswith("sb_"):
            is_sandbox_enabled = True
            break

# 2. 条件注入 SandboxTools
if is_sandbox_enabled:
    try:
        from app.services.agent.tools.sandbox_tools import SandboxTools
        # 注入工具并绑定 session_id
        tools.append(SandboxTools(session_id=session_id))
        logger.info(f"Injected Sandbox tools for agent {agent_model.name}")
        
        # 3. 追加系统提示词 (Prompt Injection)
        sb_instructions = """
## Sandbox Capabilities
You have access to a secure E2B sandbox environment. You can:
1. Execute Python code using `run_code`.
2. Run shell commands using `run_shell`...
"""
        if "Sandbox Capabilities" not in instructions:
            instructions += "\n" + sb_instructions
    except Exception as e:
        logger.error(f"Failed to inject Sandbox tools: {e}")
```

### 3.2 实际执行实现 (`sandbox_tools.py`)
虽然存在 `shell.py`，但 Agno 通过 `SandboxTools` 提供了安全的 Shell 执行方式：

- **文件**: `backend/app/services/agent/tools/sandbox_tools.py`
- **机制**: `run_shell` 方法不直接在容器运行命令，而是将其封装为 Python `subprocess` 代码，通过 `codebox_service` 在 E2B 沙箱中执行。

```python
    async def run_shell(self, command: str) -> str:
        # ...
        wrapper_code = f"""
import subprocess
try:
    result = subprocess.run('{command}', shell=True, ...)
# ...
"""
        return await self.run_code(wrapper_code)
```

## 4. 默认配置参数

要启用 E2B 集成，Agent 的配置（数据库 `agent` 表的 `skills_config` 字段）需满足以下结构：

```json
{
  "sandbox": {
    "enabled": true
  }
}
```

环境依赖（`.env`）：
- `E2B_API_KEY`: 必填，E2B 平台密钥。
- `E2B_TEMPLATE_ID`: 选填，自定义沙箱模板 ID。

## 5. 验证与复现

已创建自动化测试脚本 `tests/validate_e2b_integration.py` 用于验证上述逻辑。

**运行测试命令**:
```bash
pytest tests/validate_e2b_integration.py
```

**测试用例覆盖**:
1. `test_e2b_integration_logic`: 
   - 验证当 `skills_config={"sandbox": {"enabled": True}}` 时，`SandboxTools` 被正确注入。
   - 验证当配置为 `False` 时，工具未被注入。
2. `test_shell_and_e2b_tools_exclusion`:
   - 验证 `ShellTools` (本地 Shell) 和 `E2BTools` (冗余实现) 不会被默认加载，确保安全性。

## 6. 结论与建议

1. **现状确认**: Agno 默认集成了 E2B 能力，但采用了“白名单”策略（需显式开启）。
2. **代码冗余**: `app/services/agent/tools/e2b.py` 目前未被使用，建议标记为 Deprecated 或考虑在未来替换 `sandbox_tools.py` 以获得更丰富的功能。
3. **安全性**: `app/services/agent/tools/shell.py` 虽存在但默认禁用，符合安全最佳实践。
