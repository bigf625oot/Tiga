- 模式选择卡片 (Quick模式, Solo模式, etc.)
- 代码位置 : SmartQAChatArea.vue
- 实现逻辑 : 这里遍历了 modes 数组来渲染那 5 个卡片。
- 数据来源 : 模式的定义（如图标、名称、描述）位于常量文件 index.ts 中。
- 输入框与联网搜索 (描述您的需求..., 联网搜索)
- 代码位置 : SmartQAInput.vue
- 实现逻辑 : SmartQAChatArea 引入了 SmartQAInput 组件。其中“联网搜索”开关位于 SmartQAInput.vue:L41-L49 。
- 快捷指令 (帮我把文档翻译成中文)
- 代码位置 : SmartQAChatArea.vue
- 实现逻辑 : 这里渲染了 userScripts 列表，对应截图下方的快捷指令卡片。
  -附件弹窗：AttachmentDialog.vue
    

文件： ChatCard.vue 这是单条消息的渲染组件，负责将解析后的数据展示给用户。

- 思考过程 ：使用 <details> 标签实现可折叠的“思考过程”面板（代码中对应 v-if="parsed.think" ）。
- 图表展示 ：如果回复中包含图表数据，会通过 ChartFrame 组件渲染 ECharts 图表。
- Markdown 渲染 ：普通的文本回复会通过 v-html="parsed.html" 渲染为富文本。

