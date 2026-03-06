# OpenClaw 服务模块

OpenClaw 提供网关通信、节点管理、任务解析与下发等能力，支持分布式执行：任务分片、节点优选、故障转移、会话亲和、智能体记忆与实时状态同步。

## 目录结构

```
openclaw/
├── __init__.py
├── README.md
├── clients/
│   ├── __init__.py
│   ├── agno.py            # AgnoGatewayClient 控制面（WebSocket）
│   └── node.py            # OpenClawWsClient 数据面（节点监控/指令）
├── common/
│   ├── __init__.py
│   └── errors.py          # 异常类型（Dispatch/Parsing 等）
├── observability/
│   ├── __init__.py
│   └── dispatch_metrics.py # Prometheus 指标封装
├── gateway/
│   ├── service.py         # 网关服务编排
│   ├── dispatch.py        # 任务下发（WS-only）
│   ├── sharding.py        # 分片策略
│   ├── tools.py           # 工具封装（WS 执行 + 可选本地 fallback）
│   ├── consistency.py     # 一致性保障
│   ├── agent.py           # Agent 集成
│   └── connection.py      # 连接管理（如需）
├── node/
│   ├── auth.py            # 设备认证（Ed25519 / deviceToken）
│   ├── discovery.py       # 节点发现
│   ├── heartbeat.py       # 心跳
│   ├── manager.py         # 生命周期管理
│   ├── metadata.py        # 元数据管理
│   ├── monitor.py         # 节点状态监控（持久 WS）
│   └── selector/
│       ├── base.py
│       ├── tag_selector.py
│       └── least_load_selector.py
└── task/
    ├── parser.py          # 任务意图解析（LLM + 记忆召回）
    ├── prompt.py          # 提示词模板
    ├── execution.py       # 任务执行
    ├── session.py         # 会话管理与亲和性
    ├── sync.py            # 状态同步与故障转移
    └── memory/
        ├── interface.py
        ├── models.py
        └── storage.py
```

## 核心能力
- 分布式调度：分片（Broadcast/RR/Targeted）、节点选择（标签/负载）
- 会话亲和：TaskSessionManager 维护多轮上下文与节点亲和
- 智能体记忆：Redis JSON/RediSearch 存储与召回，辅助解析指代
- 实时监控：NodeMonitor 持久 WS、RTT 指标、自动重连
- 可靠下发：WS-only 下发，失败指标记录与错误分期（Phase）

## 通信与约束
- 通信模式：严格 WebSocket，HTTP 降级已移除
- 控制面客户端：AgnoGatewayClient（clients/agno.py）
- 数据面客户端：OpenClawWsClient（clients/node.py）
- 可选本地 fallback：tools.py 对 web_search/web_fetch 提供可选本地实现（若模块缺失则自动禁用）

## 环境变量

```bash
# 基础连接
OPENCLAW_BASE_URL=ws://localhost:3000           # 仅支持 ws/wss
OPENCLAW_WS_URL=ws://localhost:3000             # 可选，覆盖 OPENCLAW_BASE_URL
OPENCLAW_GATEWAY_TOKEN=your_token               # 或 OPENCLAW_TOKEN

# 设备身份（可选）
OPENCLAW_DEVICE_PRIVATE_KEY=base64_raw_32_bytes # Ed25519 种子（32字节）
OPENCLAW_DEVICE_ID=sha256(pubkey)               # 若与私钥派生不一致会警告

# Agno 控制面（可选）
OPENCLAW_AGNO_KEY=your_key
OPENCLAW_AGNO_SECRET=your_secret

# LLM 与记忆
OPENAI_API_KEY=your_key                         # 任务解析使用
REDIS_URL=redis://localhost:6379                # 记忆存储
```

## 快速开始
1. 配置环境变量并启动 Redis
2. 初始化节点监控（示例）：

```python
from app.services.openclaw.node.monitor import node_monitor
await node_monitor.start()
```

3. 使用工具执行任务（控制面走 WS）：

```python
from app.services.openclaw.gateway.tools import OpenClawTools
tools = OpenClawTools(base_url="ws://localhost:3000", all=True)
res = await tools.web_search("OpenClaw")
```

4. 进行任务下发：

```python
from app.services.openclaw.gateway.dispatch import DispatchService
service = DispatchService()
# 假设 active_nodes 已获取
result = await service.dispatch({"command": "cron.add"}, "task-123", active_nodes)
```

## 维护建议
- 统一导入路径：不再使用 `clients/http` 或 `clients/ws` 子目录
- 文档与代码同步：重构后必须同时更新 README 的目录与术语
- 指标与异常：统一使用 `observability/dispatch_metrics.py` 与 `common/errors.py`
