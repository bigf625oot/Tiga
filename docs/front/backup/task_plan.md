# Tiga 前端核心架构生产级重构专项集合 (技术债治理)

---

## 专项一：前端渲染架构生产级重构专项 (Rendering Architecture)

### 1. 核心目标 (Goals)
从第一性原理出发，解决前端 `llm-chat` 模块渲染架构中的“多重协议耦合”问题。废弃脆弱的“文本正则硬切”方案，全面拥抱“SSE 结构化事件驱动”模型，实现 100% 的渲染可预测性，将应用从“能跑的 Demo”升级为“稳定可扩展的生产级 AI Native 平台”。

### 2. 背景与现状 (Context)
当前系统存在三套并行的解析协议，导致极大的维护成本和潜在的崩溃风险：
1. **老链路（文本正则硬切）**：`useMessageParser.ts` 强依赖正则表达式（如 `::: echarts :::`, ````sql`）来切分纯文本，极易在流式渲染中崩溃。
2. **新链路（AST/HAST 树解析）**：`MarkdownRenderer.vue` 通过 `remark/rehype` 拦截 `<document-card>` 等自定义标签。
3. **终极链路（SSE 结构化事件驱动）**：后端已支持在 `AgentEvent` 中下发 `tool_call`, `artifact` 等结构化数据，由前端 `MessageRenderer.vue` 和 `BlockRendererRegistry.ts` 动态渲染。

现状导致：
- 渲染逻辑分散（组件解析、Composable解析、AST解析）。
- 对后端提示词过度依赖（必须让大模型吐出特定的字符串格式）。
- 扩展性差（新增模态需要修改底层解析器，违背开闭原则）。

### 3. 架构准则 (Architecture Principles)
- **单一真实来源 (Single Source of Truth)**：所有富交互组件的数据必须来源于后端的结构化事件流 (SSE Tool/Artifact Events)，而非纯文本的正则提取。
- **职责分离 (Separation of Concerns)**：Markdown 解析器只负责文本和基础代码高亮；业务卡片完全由 `BlockRenderer` 接管。
- **开闭原则 (Open-Closed Principle)**：新增任何类型的渲染块，不应修改核心解析链路，只需在 Registry 中注册新组件。

### 4. 执行阶段 (Phases)

#### Phase 1: 渲染器体系瘦身与剥离 (Frontend Parser Refactoring)
**状态**: 🔴 Not Started
- [ ] **重构 `useMessageParser.ts`**：
  - 移除对 `::: echarts`, ````sql`, `[DocCard:]`, `::: file` 的状态机解析逻辑。
  - 仅保留对 `<think>` 标签的解析（因其本质上是思维链文本的推流特性）。
- [ ] **清理 `MarkdownRenderer.vue` 越权逻辑**：
  - 移除 AST 层面拦截 `DocumentCard`, `ArtifactCard` 的逻辑。
  - 恢复其作为纯粹的 Markdown 和 Code 高亮渲染器的本质。

#### Phase 2: SSE 事件与 Block 体系的全面接管 (Event-to-Block Pipeline)
**状态**: 🔴 Not Started
- [ ] **强化 `useChatSession.ts` 的事件转换层**：
  - 确保后端的 `artifact` 事件能够被准确映射为前端的 `ResourceBlock`。
  - 确保图表生成工具的 `tool_output` 能够被映射为 `VisualizationBlock`。
  - 确保知识库引用工具能够映射为 `ReferencesBlock` 或 `ResourceBlock`。
- [ ] **完善 `BlockRendererRegistry.ts`**：
  - 审查现有的 `ResourceBlockRenderer`, `VisualizationBlockRenderer`，确保它们能够独立处理完整的结构化数据。
  - 添加缺失的适配层（如果后端发来的结构与前端 Block 结构有微小差异）。

#### Phase 3: 后端协议收敛与 Tool Call 对齐 (Backend Protocol Alignment)
**状态**: 🔴 Not Started
- [ ] **排查后端 Prompt 与工具定义**：
  - 全面扫描后端的 System Prompts，移除所有类似于“请用 `::: echarts :::` 格式输出图表”的指令。
  - 确保大模型执行动作时（如生成文件、画图、引用文献），100% 通过 Tool Call 触发。
- [ ] **梳理 `agent_event.py`**：
  - 确保所有非文本的多模态产物，都能通过 `artifact` 或 `tool_output` 事件规范下发。

#### Phase 4: 全链路回归测试与验收 (Production Readiness Validation)
**状态**: 🔴 Not Started
- [ ] 验证 Quick 模式下的纯文本对话、代码生成、思维链（<think>）是否正常流式输出。
- [ ] 验证 Workflow/Solo 模式下的工具调用轨迹（Tool Call Timeline）是否正确渲染。
- [ ] 验证文件生成（Artifact）、图表渲染（Echarts）是否通过新的 Block 机制成功呈现。
- [ ] 验证知识库引用溯源（DocCard）是否正常工作。

### 5. 预期收益 (Expected Outcomes)
1. **消灭正则解析带来的 CPU 性能损耗与卡顿**。
2. **彻底解决大模型输出格式不稳定导致的 UI 破损问题**（因为结构化 JSON 会在后端/大模型层做校验，到达前端一定是强类型的）。
3. **建立极简的插件化渲染架构**，未来新增任何模态（如视频播放卡片），前端工作量从“修改核心解析器”降维到“写一个 Vue 组件并在 Registry 中注册”。

---

## 专项二：API 边界防腐层与类型安全重构专项 (Anti-Corruption Layer & Type Safety)

### 1. 核心目标 (Goals)
遵循“第一性原理”和“领域驱动设计 (DDD)”，彻底重构前端与后端的 API 通信边界。剥离 Service 层的网络协议细节，建立全局防腐层（ACL），并实现从端到端的 100% 静态类型安全。

### 2. 背景与现状 (Context)
当前以 `chatService.ts` 为代表的服务层代码存在严重的职责越界与抽象泄漏：
1. **协议外壳耦合**：Service 层充斥着防御性的 `if ('data' in raw)` 逻辑，用于兼容不同风格的后端响应（如 `{code: 200, data: ...}`）。
2. **类型裸奔**：大量使用 `any` 类型（如 `m: any`），放弃了 TypeScript 的静态分析能力，运行时风险极高。
3. **业务逻辑与数据清洗混杂**：DTO 到 Domain 模型的映射逻辑直接硬编码在异步网络请求的上下文中，缺乏可测试性。

### 3. 架构准则 (Architecture Principles)
- **防腐层前置 (Anti-Corruption Layer)**：所有的 HTTP 协议解包、异常拦截必须在全局拦截器层完成，Service 层只允许接收纯净的领域实体 (Domain Entity)。
- **类型即契约 (Type as Contract)**：禁止在核心数据流转中使用 `any`，全面引入类型守卫 (Type Guard) 进行校验与推导。
- **数据清洗纯函数化 (Pure Function Mapping)**：DTO 到前端视图模型 (View Model) 的转换必须抽离为 100% 覆盖单元测试的纯函数。

### 4. 执行阶段 (Phases)

#### Phase 1: 基础设施下沉与拦截器重构 (Infrastructure & Interceptor)
**状态**: 🔴 Not Started
- [ ] **全局响应拦截器 (Axios Interceptor) 升级**：
  - 统一处理 `{code, data, message}` 标准外壳的剥离，抹平后端数据结构的历史遗留问题。
  - 统一处理业务级错误码并转换为标准的 Error 对象抛出。
- [ ] **清理 Service 层冗余逻辑**：
  - 移除 `chatService.ts` 及其他 Service 中对 `raw.data` 的嗅探和防御性拆包代码。

#### Phase 2: 领域模型映射分离 (Domain Mapping Separation)
**状态**: 🔴 Not Started
- [ ] **抽离 Mapper 纯函数**：
  - 编写独立的 `mapMessageDTOToDomain` 等纯函数，处理 `reasoning_content -> reasoning` 等异构字段的抹平。
- [ ] **补充单元测试**：
  - 为 Mapper 函数提供不同版本后端响应的 Mock 数据，确保向后兼容性的 100% 测试覆盖率。

#### Phase 3: 类型契约与静态校验 (Type Safety)
**状态**: 🔴 Not Started
- [ ] **消灭核心路径的 `any`**：
  - 替换 `chatService.ts` 等文件中的 `m: any` 为强类型定义，完善接口层面的类型提示。
- [ ] **严格的 DTO 与 Domain 模型定义**：
  - 区分后端返回的 DTO (Data Transfer Object) 接口和前端使用的 Domain 模型接口，防止后端字段污染前端组件。

### 5. 预期收益 (Expected Outcomes)
1. **极简的服务层代码**：Service 层代码量将大幅减少，只保留核心的请求发送与数据分发逻辑。
2. **100% 的可测试性**：复杂的映射和清洗逻辑被剥离为纯函数，可以无缝接入单元测试。
3. **免疫后端协议变更**：后端任何非破坏性的外壳变更，只需修改一层 Interceptor，业务逻辑完全无感。