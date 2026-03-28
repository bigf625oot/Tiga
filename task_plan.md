# 任务计划：大模型对话卡片 UI 架构重构 (对标 P10 标准)

## 目标与定位 (Goal & Vision)
- **目标**: 重新设计和架构大模型对话界面（支持 solo、team、workflow 等模式，以及 thought、plan_step、tool、sandbox、web_search、kb_retrieval、content 等多种消息实体），并参考 `ai-sdk/vue` UI 框架的最佳实践。
- **P10 交付标准**:
  - **第一性原理**: 摒弃基于 `if-else` 的消息类型渲染，建立基于状态机或策略模式的高扩展性渲染引擎。
  - **降维打击**: 将复杂的多种模式、多种状态抽象为统一的协议和渲染管线。
  - **性能极致**: 确保长列表渲染、复杂动画和高频流式数据更新的极致性能（避免不必要的重渲染）。
  - **全局感知**: 评估改动对当前 `features/chat` 和 `features/qa` 的影响。

## 阶段规划 (Phases)

### Phase 1: 现状调研与架构评估 (Current State Analysis) ✅
- [x] 检查现有的 `features/chat/components` 和 `features/qa/components`。
- [x] 分析现有模式 (solo, team, workflow) 和消息状态 (thought, plan, tool, etc.) 的实现方式。
- [x] 记录调研发现到 `findings.md`。

### Phase 2: 核心架构设计 (Architecture Design) ✅
- [x] 设计统一的消息状态机模型 (Message State Machine) 与类型定义（新增 Sandbox, KbRetrieval）。
- [x] 设计基于策略模式 (Strategy Pattern) 的组件渲染器映射表 (`BlockRendererRegistry`)。
- [x] 设计组件间的通信契约 (Props down, Events up) 与插槽 (Slots) 策略。

### Phase 3: 核心组件实现 (Implementation - Core) ✅
- [x] 将 `MessageRenderer.vue` 中的 200 行 `if-else` 树彻底推翻，重构为 `<component :is="...">` 的高解耦架构。
- [x] 实现针对各类子状态的原子渲染器 (`SearchBlockRenderer`, `SandboxBlockRenderer` 等)。
- [x] 完成全局类型检查 (`vue-tsc --noEmit` 通过)。

### Phase 4: 模式适配与性能优化 (Adaptation & Performance) ✅
- [x] 在 `SmartQA.vue` 中提供 (Provide) 统一的全局上下文 `ChatContextKey`。
- [x] 适配 Solo, Team, Workflow 三种顶层模式的上下文隔离，将其注入到 `MessageRenderer.vue` 中。
- [x] 保持自定义 SSE 流协议优势，放弃硬套 `ai-sdk` fetch 逻辑，但全盘吸收其 `toolInvocations` 和组件化渲染的设计理念（体现了 P10 对框架选型的 Trade-off）。

## 当前状态
- **当前阶段**: 已完成。
- **状态**: 架构基建已完成。代码解耦度大幅提升，`vue-tsc` 无报错。