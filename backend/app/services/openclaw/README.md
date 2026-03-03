# OpenClaw Service Module

OpenClaw 核心服务模块，提供网关通信、节点管理、任务解析与下发等功能。
新增分布式执行支持，包括任务分片、节点优选、元数据管理、故障转移、会话管理、智能体记忆及实时状态同步能力。

## 目录结构

```
openclaw/
├── __init__.py             # 模块导出（Barrel）
├── clients/                # 外部客户端
│   ├── http/               # HTTP 客户端
│   └── ws/                 # WebSocket 客户端
├── gateway/                # 网关交互逻辑
│   ├── gateway/            # 网关核心服务
│   │   ├── gateway_service.py # 网关服务入口
│   │   ├── ws_handler.py      # WebSocket 连接管理（分片、限流、去重）
│   │   └── consistency.py     # 数据一致性检查与补偿
│   ├── dispatch/           # 任务下发服务
│   │   ├── dispatch_service.py # 任务分发逻辑
│   │   └── sharding.py         # 分片策略
│   └── agent/              # Agent 工具封装
├── node/                   # 节点管理
│   ├── manager/            # 节点生命周期与元数据管理
│   │   ├── node_manager_service.py
│   │   └── metadata.py         # 元数据同步逻辑
│   ├── monitor/            # 节点状态监控
│   │   ├── heartbeat.py        # 高频心跳与环形缓冲
│   │   └── node_monitor_service.py
│   ├── selector/           # 节点选择器
│   │   ├── base.py
│   │   ├── tag_selector.py     # 基于标签筛选
│   │   └── least_load_selector.py # 基于负载优选
│   ├── discovery/          # 节点发现
│   └── auth/               # 设备认证
├── task/                   # 任务处理
│   ├── parser/             # 任务意图解析
│   │   ├── task_parser_service.py # LLM 解析与记忆召回
│   │   └── prompt.py              # 提示词模板
│   ├── memory/             # 智能体记忆模块
│   │   ├── interface.py    # 记忆接口定义
│   │   ├── models.py       # 记忆数据模型
│   │   └── storage.py      # Redis 存储与检索实现
│   ├── session/            # 任务会话管理
│   │   └── session_manager.py # 会话上下文与亲和性管理
│   └── worker/             # 任务执行与状态同步
│       ├── task_worker_service.py
│       └── status_sync.py     # 状态同步逻辑
└── utils/                  # 工具类
    ├── metrics.py          # 监控指标
    └── exception.py        # 异常定义
```

## 适用场景

本模块适用于以下复杂分布式场景：

1.  **大规模设备集群管理**
    *   **场景**: 管理数千台分布在不同地域的边缘计算节点或 IoT 设备。
    *   **能力**: 利用 `Gateway Sharding` 和 `Heartbeat Compression` 支撑高并发心跳；通过 `TagSelector` 实现基于地理位置或硬件特性的精准任务下发。

2.  **长流程任务与智能体对话**
    *   **场景**: 用户与智能体进行多轮对话，分步执行复杂操作（如：先检查服务器状态，再根据结果执行重启）。
    *   **能力**: `TaskSessionManager` 维持会话上下文；`Agent Memory` 召回历史记忆，解决“它”、“上一步”等指代消解问题；`Session Affinity` 确保任务在同一节点连续执行。

3.  **高可靠性自动化运维**
    *   **场景**: 执行关键的自动化运维脚本，要求任务不丢失、执行结果实时反馈。
    *   **能力**: `ConsistencyManager` 确保状态数据一致性；`Failover` 机制在节点宕机时自动迁移任务；`Ring Buffer` 防止网络抖动导致的状态丢失。

## 与原生 OpenClaw 的区别

| 特性 | 原生 OpenClaw (Base) | Tiga OpenClaw (Enhanced) | 优势 |
| :--- | :--- | :--- | :--- |
| **任务分发** | 简单的点对点或随机分发 | **智能分片与优选** (Tag/LeastLoad/Sharding) | 支持复杂策略，优化资源利用率 |
| **会话管理** | 无状态，单次任务独立 | **会话亲和性 (Sticky Session)** | 支持多轮对话和上下文连续性 |
| **记忆能力** | 无 | **长期记忆与上下文召回** (Redis Vector/JSON) | 智能体更“聪明”，能理解上下文 |
| **通信效率** | 标准 HTTP/WS | **高频压缩心跳 + 环形缓冲 + 连接分片** | 支撑 10x 以上的并发连接规模 |
| **数据一致性**| 弱一致性 | **强一致性检查 (CRC32) + 自动补偿** | 数据更可靠，自动修复脏数据 |
| **可观测性** | 基础日志 | **多维 Metrics + 审计日志** | 更易于监控和故障排查 |

## 核心功能

### 1. 分布式任务调度
- **任务分片 (Sharding)**: 支持广播 (Broadcast)、轮询 (Round-Robin)、指定目标 (Targeted) 等多种分发策略。
- **节点选择 (Selector)**: 
  - `TagSelector`: 基于标签的精准匹配。
  - `LeastLoadSelector`: 基于负载（RTT/任务数）的节点优选。
- **会话管理 (Session)**: 
  - `TaskSessionManager`: 维护多轮对话或任务链的会话上下文。
  - **会话亲和性 (Session Affinity)**: 确保同一会话的任务优先分发到同一节点，保持上下文连续性。

### 2. 智能体记忆 (Agent Memory)
- **记忆存储**: 基于 Redis JSON + RediSearch 实现结构化记忆存储。
- **上下文召回**: 解析任务时自动检索最近对话历史和语义相关的长期记忆。
- **指代消解**: 利用召回的上下文增强 LLM 提示词，解决“它”、“上一步”等指代不明问题。

### 3. 实时状态同步与一致性
- **高频心跳**: 支持 500ms 级心跳上报，内置环形缓冲区 (Ring Buffer) 防止数据丢失。
- **WebSocket 优化**: 
  - **连接分片**: 支持高并发连接管理。
  - **背压限流**: 使用令牌桶算法保护网关。
  - **消息去重**: 基于 Sequence ID 过滤重复消息。
- **一致性保障**: 
  - **脏数据检测**: 实时校验 CRC32 和时间戳顺序。
  - **自动补偿**: 发现异常自动触发 `force_sync` 全量同步，并标记节点状态。

### 4. 节点元数据管理
- **元数据同步**: 自动从节点心跳中提取硬件资源（CPU/内存）、IP 归属地及自定义标签。
- **标签筛选**: 提供 API 支持 LLM 根据环境标签筛选可用节点。

### 5. 高可用与故障转移
- **心跳检测**: 实时监控节点健康状态，自动标记离线节点。
- **故障转移 (Failover)**: 任务执行期间节点掉线，系统自动感知并将任务重新分发至其他可用节点。

## 快速开始

### 环境变量

确保 `.env` 文件中配置了以下变量：

```bash
OPENCLAW_BASE_URL=http://localhost:3000
OPENCLAW_GATEWAY_TOKEN=your_token
OPENAI_API_KEY=your_key  # 用于任务解析
REDIS_URL=redis://localhost:6379 # 用于记忆存储
```
