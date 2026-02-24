# 沙箱模块全流程测试方案 (Sandbox Module Full-Process Test Scheme)

## 1. 测试目标 (Objectives)
构建一套完整的自动化测试体系，覆盖沙箱模块的生命周期管理、代码执行、资源隔离及安全策略，确保沙箱服务在隔离性、稳定性、并发性能及异常处理能力上符合预期。

## 2. 测试范围 (Scope)
*   **核心服务 (`E2BSandboxService`)**:
    *   沙箱实例管理（创建、复用、销毁）
    *   代码执行（Python 代码运行、标准输出/错误流捕获）
    *   文件操作（上传、下载、生成文件）
    *   依赖管理（pip 包安装）
*   **API 接口**:
    *   REST API (`POST /sandbox/run`)：同步执行请求
    *   WebSocket API (`/sandbox/ws/{session_id}`)：流式执行与实时交互
*   **安全与异常**:
    *   代码超时控制
    *   非法代码拦截（如无限循环、高资源占用模拟）
    *   API Key 缺失或无效处理

## 3. 测试策略 (Strategy)

### 3.1 单元测试 (Unit Testing)
*   **工具**: `pytest`, `unittest.mock`, `pytest-asyncio`
*   **Mock 策略**: 对 `e2b_code_interpreter.Sandbox` 进行深度 Mock，模拟 E2B 服务的各种响应（成功、失败、超时、网络错误），避免测试依赖外部网络和消耗额度。
*   **覆盖率目标**: 核心逻辑分支覆盖率 ≥ 90%。

### 3.2 集成测试 (Integration Testing)
*   **工具**: `pytest`, `FastAPI TestClient`
*   **场景**:
    *   端到端流程：API 请求 -> 服务层 -> Mock E2B -> 结果返回 -> 数据库/文件持久化。
    *   WebSocket 交互：建立连接 -> 发送代码 -> 接收流式输出 -> 接收最终结果 -> 关闭连接。

### 3.3 性能基准测试 (Performance Benchmarking)
*   **工具**: `locust` 或自定义 Python 脚本
*   **指标**:
    *   沙箱启动延迟 (Startup Latency)
    *   代码执行响应时间 (Execution Latency)
    *   并发执行成功率 (Concurrency Success Rate)

## 4. 测试环境 (Environment)
*   **本地开发环境**: Windows/Linux/MacOS, Python 3.10+
*   **CI/CD**: GitHub Actions (Ubuntu-latest)
*   **依赖**: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`, `websockets`

## 5. 详细测试用例 (Test Cases)

### 5.1 服务层测试 (`tests/sandbox/test_service.py`)
| 用例 ID | 描述 | 预期结果 | 优先级 |
| :--- | :--- | :--- | :--- |
| SVC-001 | 初始化沙箱 (无 Session ID) | 创建新 E2B 实例，返回新 ID | P0 |
| SVC-002 | 复用沙箱 (有 Session ID) | 连接现有实例，ID 不变 | P0 |
| SVC-003 | 执行简单 Python 代码 | 返回 stdout "Hello World" | P0 |
| SVC-004 | 执行代码并生成文件 | 返回结果包含文件路径和类型 | P1 |
| SVC-005 | 执行代码抛出异常 | 返回 stderr 包含错误堆栈 | P1 |
| SVC-006 | 上传文件到沙箱 | 文件存在于沙箱指定路径 | P1 |
| SVC-007 | 从沙箱下载文件 | 获取文件二进制内容 | P1 |
| SVC-008 | E2B 服务不可用 | 抛出 `SandboxError` | P2 |

### 5.2 API 层测试 (`tests/sandbox/test_api.py`)
| 用例 ID | 描述 | 预期结果 | 优先级 |
| :--- | :--- | :--- | :--- |
| API-001 | POST /run (同步执行) | HTTP 200, JSON 包含执行结果 | P0 |
| API-002 | POST /run (缺少代码) | HTTP 422 Unprocessable Entity | P1 |
| API-003 | WS /ws/{id} (流式执行) | 连接成功，收到 stdout 消息 | P0 |
| API-004 | WS /ws/{id} (执行错误) | 收到 stderr 消息 | P1 |

## 6. 交付物 (Deliverables)
1.  测试代码库 (`backend/tests/sandbox/`)
2.  测试覆盖率报告 (`coverage.xml`)
3.  性能基准测试脚本 (`backend/tests/performance/sandbox_bench.py`)
4.  CI/CD 配置文件更新 (`.github/workflows/sandbox_test.yml`)
