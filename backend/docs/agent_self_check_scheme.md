# 智能体全功能自检方案 (Agent Full Function Self-Check Scheme)

## 1. 自检目标与验收标准 (Objectives & Acceptance Criteria)

### 1.1 核心目标
对智能体系统实施一次端到端、覆盖前后端所有核心模块的完整功能自检，确保系统在高负载、复杂场景下的稳定性、准确性和可用性。

### 1.2 验收标准 (Acceptance Criteria)
| 指标项 | 目标值 | 说明 |
| :--- | :--- | :--- |
| **可用性 (Availability)** | ≥ 99.9% | 系统核心功能无阻断性故障 |
| **延迟 (Latency)** | P99 ≤ 800 ms | 端到端响应时间 (不含 LLM 生成耗时) |
| **工具调用成功率** | ≥ 98% | Agent 调用外部工具的准确性 |
| **记忆召回率** | ≥ 95% | 上下文关联的准确性 |
| **知识库查全率** | ≥ 90% | RAG 检索覆盖关键信息的能力 |
| **并发支持** | ≥ 50 QPS | 单节点并发处理能力 |
| **测试覆盖率** | ≥ 90% | 核心模块单元测试分支覆盖率 |

---

## 2. 详细自检计划 (Detailed Plan)

### 2.1 阶段划分
1.  **准备阶段 (Day 1-2)**: 环境搭建、数据准备、测试用例评审。
2.  **单元测试阶段 (Day 3-5)**: 后端/前端核心模块单元测试编写与执行。
3.  **集成测试阶段 (Day 6-8)**: 端到端链路测试、接口测试。
4.  **专项测试阶段 (Day 9)**: 性能测试、安全测试、异常恢复测试。
5.  **验收与修复 (Day 10)**: 缺陷修复、回归测试、输出报告。

### 2.2 环境要求
*   **Staging 环境**: 独立部署，与生产环境配置一致。
*   **数据快照**: 预置 1000+ 条知识库数据，50+ 个历史会话。
*   **Mock 服务**: 对外部 API (OpenAI, Search API) 进行 Mock，确保测试稳定性。

### 2.3 责任人
*   **测试负责人**: QA Lead
*   **后端开发**: Backend Lead
*   **前端开发**: Frontend Lead
*   **运维支持**: DevOps Engineer

---

## 3. 完整 Todo List (Implementation Tasks)

### 3.1 基础设施 (Infrastructure)
- [ ] 搭建 Staging 环境 (K8s/Docker Compose)
- [ ] 配置 CI/CD 流水线 (GitHub Actions)
- [ ] 集成 SonarQube 代码质量扫描
- [ ] 部署 Prometheus + Grafana 监控

### 3.2 测试用例开发 (Test Development)
- [ ] 编写核心 Agent 模块单元测试 (Backend)
- [ ] 编写前端组件单元测试 (Frontend)
- [ ] 开发 20 条核心链路集成测试脚本
- [ ] 准备性能测试脚本 (Locust/JMeter)

### 3.3 专项测试 (Specialized Testing)
- [ ] 执行全量知识库检索精度测试
- [ ] 模拟外部 API 限流/故障场景
- [ ] 安全漏洞扫描 (SQL注入, XSS)

---

## 4. 全量自检项清单 (Checklist - 100+ Items)

### 4.1 后端 (Backend) - 30项
*   [ ] **Agent Core**: `Agent` 初始化参数校验 (自动, P0)
*   [ ] **Agent Core**: `run()` 方法异常处理 (自动, P0)
*   [ ] **Workflow**: 步骤流转逻辑 (`plan` -> `execute` -> `reflect`) (自动, P0)
*   [ ] **Memory**: 会话历史写入/读取 (自动, P0)
*   [ ] **Memory**: 长期记忆 (User Profile) 更新 (自动, P1)
*   [ ] **Tools**: DuckDuckGo 搜索工具调用 (手动, P1)
*   [ ] **Tools**: Calculator 工具精度 (自动, P1)
*   [ ] **Tools**: SQL 查询生成准确性 (自动, P0)
*   [ ] **RAG**: 向量检索准确性 (Top-K) (自动, P0)
*   [ ] **RAG**: 混合检索 (Keyword + Vector) (自动, P1)
*   ... (更多项见完整 Excel 附件)

### 4.2 前端 (Frontend) - 25项
*   [ ] **Chat UI**: 消息气泡渲染 (Markdown/Code) (手动, P0)
*   [ ] **Chat UI**: 流式响应 (Streaming) 渲染流畅度 (手动, P0)
*   [ ] **Knowledge Graph**: 图谱节点点击交互 (手动, P1)
*   [ ] **Session**: 会话列表加载与切换 (自动, P1)
*   [ ] **Settings**: 模型参数配置保存 (自动, P2)
*   ...

### 4.3 算法与模型 (AI/Algorithm) - 15项
*   [ ] **Prompt**: System Prompt 注入防御 (自动, P0)
*   [ ] **Prompt**: 模板变量替换正确性 (自动, P1)
*   [ ] **Model**: 模型切换 (OpenAI -> Anthropic) (手动, P1)
*   ...

### 4.4 数据 (Data) - 10项
*   [ ] **Database**: 数据库连接池稳定性 (自动, P0)
*   [ ] **Vector DB**: 索引构建速度 (自动, P1)
*   ...

### 4.5 运维 (Ops) - 10项
*   [ ] **Logs**: 核心链路日志完整性 (TraceID) (自动, P0)
*   [ ] **Metrics**: API 响应时间监控 (自动, P1)
*   ...

### 4.6 安全 (Security) - 5项
*   [ ] **Auth**: JWT Token 校验 (自动, P0)
*   [ ] **API**: 接口限流 (Rate Limiting) (自动, P1)
*   ...

### 4.7 合规 (Compliance) - 5项
*   [ ] **Content**: 敏感词过滤 (自动, P0)
*   [ ] **Privacy**: 用户数据脱敏 (自动, P1)
*   ...

---

## 5. 单元测试全集 (Unit Test Suite Strategy)

### 5.1 测试框架
*   **Backend**: `pytest` + `pytest-asyncio` + `pytest-cov`
*   **Frontend**: `Vitest` + `Vue Test Utils`

### 5.2 核心覆盖模块
*   `backend/app/services/agent/service.py`: 覆盖 Agent 生命周期。
*   `backend/app/workflow/steps/*.py`: 覆盖每个 Workflow 步骤 (Plan, Execute, Reflect)。
*   `backend/app/crud/crud_chat.py`: 覆盖 Memory (会话历史) 读写。
*   `backend/app/services/rag/`: 覆盖 RAG 检索逻辑。

### 5.3 示例代码 (Backend)
```python
# tests/test_agent_execution.py
import pytest
from app.services.agent import AgentService

@pytest.mark.asyncio
async def test_agent_run_success():
    agent = AgentService()
    response = await agent.run(query="Hello", session_id="test_session")
    assert response.status == "completed"
    assert len(response.messages) > 0
```

---

## 6. 完整链路集成测试 (Integration Scenarios)

### 场景 1: 用户新建会话 -> 多轮对话 -> 工具调用 -> 记忆更新
1.  **新建会话**: 调用 `POST /api/sessions`，断言返回 `session_id`。
2.  **发送消息**: 调用 `POST /api/chat` (query="查询北京天气")。
3.  **验证工具调用**: 检查日志/Mock，确认调用了 `search_tool`。
4.  **验证响应**: 检查返回内容包含 "北京" 和 "天气"。
5.  **发送后续消息**: 调用 `POST /api/chat` (query="那上海呢？")。
6.  **验证记忆**: 确认 Agent 理解 "那" 指代 "查询天气"。
7.  **验证持久化**: 查询数据库，确认两条消息均已保存。

### 场景 2: 知识库上传 -> 索引构建 -> RAG 检索
1.  **上传文档**: 调用 `POST /api/knowledge/upload` (file="test.pdf")。
2.  **触发索引**: 确认后台任务启动。
3.  **轮询状态**: 等待索引状态变为 `ready`。
4.  **执行检索**: 调用 `POST /api/rag/search` (query="文档关键词")。
5.  **验证结果**: 确认返回结果包含文档片段。

---

## 7. 自动化测试流水线 (CI/CD Pipeline)

### GitHub Actions Workflow (`.github/workflows/self_check.yml`)
*   **Trigger**: `push` (main/develop), `pull_request`
*   **Jobs**:
    *   `unit-test-backend`: 运行 pytest，生成覆盖率报告。
    *   `unit-test-frontend`: 运行 vitest。
    *   `integration-test`: 启动 Docker Compose 环境，运行端到端测试。
    *   `report`: 汇总测试结果，发送通知 (Slack/Email)。

---

## 8. 风险与应急 (Risks & Contingency)

| 风险点 | 触发条件 | 应急预案 |
| :--- | :--- | :--- |
| **外部 API 限流** | OpenAI/Search API 返回 429 | 自动切换至备用模型/Mock 数据；前端提示“服务繁忙”。 |
| **向量库崩溃** | LanceDB 内存溢出 | 降级为纯关键词检索 (BM25)；重启向量库服务。 |
| **响应超时** | 单次请求 > 60s | 异步处理模式；前端显示进度条；后台重试机制。 |

---

## 9. 交付物 (Deliverables)

1.  **自检执行报告**: PDF/HTML 格式，包含通过率、耗时统计。
2.  **测试代码库**: `tests/` 目录下的所有测试脚本。
3.  **缺陷清单**: Jira/Issue 列表，包含优先级和修复状态。
4.  **性能基线文档**: 记录当前版本的 QPS 和 Latency 指标。
