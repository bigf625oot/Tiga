请重构 `adaptMessageToBlocks` 函数，采用“处理器分发”模式：

1. **解耦处理器 (Processor Decoupling)**: 
   - 创建一个 `MessageProcessor` 接口。
   - 将逻辑拆分为独立的类或函数：`PlanProcessor`, `ToolProcessor`, `ContentParser`, `MediaProcessor`, `ArtifactProcessor`。
   - 主函数只需按顺序调用这些处理器，并将结果平铺（flatten）到 blocks 数组中。

2. **工具注册表 (Tool Registry)**:
   - 不要使用硬编码的 `terminalTools` 数组。创建一个 `TOOL_HANDLER_MAP`，将工具名映射到对应的转换逻辑（如 `TerminalHandler`, `ActionHandler`, `VisualHandler`）。
   - 这样新增工具类型时，只需在注册表中添加配置，无需修改主转换逻辑。

3. **结果幂等与纯函数化**: 
   - 确保转换过程不修改原始 `message` 对象，所有中间状态通过 Context 传递。

请重构 `convertMermaidMindmapToMarkdown` 函数：

1. **引入缩进栈 (Indent Stack)**: 
   - 废除基于 `Math.round` 和硬编码 `indentStep` 的除法计算。
   - 采用“缩进栈”算法：维护一个记录当前缩进深度的数组，通过比较当前行缩进与栈顶元素的关系，精准确定 Heading 等级（# 的数量）。
   - 这种算法能完美兼容 LLM 输出的 2/4 空格混用或不规则缩进。

2. **正则清洗增强**: 
   - 提取一个 `stripMermaidDecorators` 工具函数，集中处理 `((text))`, `[[text]]`, `{{text}}` 等 Mermaid 节点形状。

1. **思考块去重 (Thought Deduplication)**: 
   - 修改逻辑：如果在 `message.content` 中检测到 `<think>` 标签并成功解析为 `ThoughtBlock`，则必须忽略（Suppress）`message.reasoning` 和 `message.meta_data.reasoning`，防止 UI 出现双重思考过程。

2. **计划状态精准化**: 
   - 废除 `Math.ceil` 平摊工具到步骤的算法。
   - **改进方案**：尝试通过 `step.id` 与 `tool.call_id` 或 `tool.step_id`（如果后端支持）进行匹配。如果不支持，退而求其次使用“名称匹配”：检查工具名是否出现在步骤文本中。如果均无法匹配，将所有工具视为“全局操作”放在计划块之后，而不是强行平摊。

3. **流式状态增强**: 
   - 在流式输出（isStreaming）过程中，确保最后一个 `ThoughtBlock` 或 `TextBlock` 的状态能实时反映 `thinking` 或 `streaming` 状态。

1. **流式 JSON 容错**: 
   - 引入一个 `partialJsonParse` 函数。在处理 `VisualizationBlock` 时，如果 `t.result` 是不完整的 JSON（常见于流式传输中），尝试补齐末尾的大括号或返回已解析的部分，以实现图表的“渐进式渲染”。

2. **文本段处理优化**: 
   - 确保 `textParts` 的收集和 `blocks.push` 逻辑在循环中能够正确处理边界情况，避免在特殊块（如 `<think>`）前后产生多余的空行或空白 TextBlock。

3. **终端块增强**: 
   - 改进 `TerminalBlock` 的命令提取：如果 `args` 已经是字符串，直接作为命令；如果解析失败，将整个 `raw_arguments` 作为 fallback。