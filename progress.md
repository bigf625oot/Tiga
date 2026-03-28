# 进度跟踪 (Progress)

## 会话记录
- **[2026-03-28]**: 启动“大模型对话卡片 UI 架构重构”任务。
  - 创建了 `task_plan.md` 和 `findings.md`。
  - 完成了代码库扫描，重点分析了 `features/chat/components/MessageRenderer.vue` 和 `features/chat/utils/MessageAdapter.ts`。
  - 确认了当前架构违背了 P10 标准中的“拒绝冗余”原则，决定采用策略模式 (Strategy Pattern) 进行重构。
  - 更新了类型定义的需求（准备增加 Sandbox 和 KB Retrieval 类型）。
  - **完成 Phase 3**: 重写了 `MessageRenderer.vue`，从近 200 行的 `if-else` 分支缩减到 `<component :is="...">` 的映射表调用，大幅提升了系统的可维护性和扩展性。
  - **完成 Phase 4**: 
    - 针对 `ai-sdk/vue` 进行了调研。决断：保持当前的 SSE 引擎，但引入其 `toolInvocation` 的思想。
    - 在 `SmartQA.vue` (顶层组件) 中通过 Vue 的 `provide` 注入了 `ChatContextKey`。
    - `MessageRenderer.vue` 通过 `inject` 获取顶层上下文并透传给具体的子 Block。
    - 修复了 `vue-tsc` 的 TypeScript 类型检查报错。

## 遇到的问题及解决方案
- **问题**: 原本的 `MessageRenderer.vue` 承担了太多的职能，导致在重构为 `<component :is>` 时，原本模板里解构出来的事件参数（如 `ref`, `id`, `path`）在子组件里类型推断丢失。
- **解决方案**: 在各个新建的 `*BlockRenderer.vue` 中补齐了强类型的 `defineEmits`，并在主渲染器中通过箭头函数 `(p: string) => ...` 显式声明了参数类型，顺利通过了 `npm run type-check`。

## 架构升级总结
本次重构完成了从“**过程式渲染**”到“**声明式/策略式渲染**”的范式转移 (Paradigm Shift)。
所有的消息渲染全部原子化为：
- `SandboxBlockRenderer.vue`
- `KbRetrievalBlockRenderer.vue`
- `SearchBlockRenderer.vue`
- `ToolBlockRenderer.vue` 等

未来如果新增任何类型（如 `WebBrowsing`, `RPA` 等），只需要：
1. 在 `types` 中新增 `Block` 定义。
2. 编写 `xxxBlockRenderer.vue`。
3. 在 `BlockRendererRegistry.ts` 中注册即可。
核心引擎 `MessageRenderer.vue` 代码将永远保持稳定，完全符合 P10 级别的 **开闭原则 (Open-Closed Principle)**。