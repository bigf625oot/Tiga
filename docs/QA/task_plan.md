# 修复 SmartQA 消息卡片显示 BUG 计划

## 目标
修复 `SmartQA.vue` (及其子组件 `ChatCard.vue`) 在所有模式下消息卡片显示的 BUG。
具体表现为：普通文本消息被错误地渲染为包含空白图表和复杂结构的“数据可视化/详情”卡片。

## 阶段

### 阶段 1: 诊断与分析 (Diagnosis)
- [ ] 检查 `frontend/src/features/qa/composables/useChart.ts`，确认 `processOption` 对空输入的处理。
- [ ] 检查 `frontend/src/features/qa/components/ChatCard.vue`，确认 `chartOption` 的计算逻辑和模板渲染条件。
- [ ] 检查 `frontend/src/features/qa/composables/useMessageParser.ts`，确认消息解析是否误判了图表配置。

### 阶段 2: 修复逻辑 (Fix)
- [ ] 修复 `useChart.ts` 或 `ChatCard.vue` 中的 `chartOption` 计算逻辑，确保无图表时返回 `null`。
- [ ] 优化 `ChatCard.vue` 的模板结构，区分“纯文本回复”和“富数据回复”。
    - 如果没有图表、SQL、Thinking，仅有文本，应显示为简洁的气泡样式。
    - 如果有富数据，才显示复杂的 Card 结构。

### 阶段 3: 验证 (Verification)
- [ ] 验证普通文本消息是否恢复正常显示。
- [ ] 验证包含图表的消息是否依然正常显示。
- [ ] 验证包含 SQL 的消息是否依然正常显示。
