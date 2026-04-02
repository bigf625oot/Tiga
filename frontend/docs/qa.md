### 1. useAgentSelection.ts (状态/交互)
- 职责 ：专门负责管理智能体（Agent）或团队（Team）的选择与切换逻辑。
- 功能点 ：
  - 维护 selectedAgentId 。
  - 维护 Agent 列表与 Team 列表。
  - 处理模式切换（Chat/Workflow/Team 等）时默认选中项的降级与同步。
- 架构意义 ：解耦了会话状态与角色选择，使得切换对话对象时不需要影响底层网络请求的状态机。
### 2. useAttachments.ts (领域模型)
- 职责 ：封装对话输入框中的文件附件管理。
- 功能点 ：
  - 本地上传、解析、删除文件。
  - 将附件转换为对话协议能接受的数据结构（Base64 或 URL 引用）。
- 架构意义 ：处理富文本输入的脏活累活，保证核心对话接口只看到干净的 Payload。
### 3. useSmartQALayout.ts (UI 编排)
- 职责 ：掌控左右双栏布局（Chat 区和 Task 区）的响应式控制。
- 功能点 ：
  - 判断是否需要折叠面板（Responsive 视口处理）。
  - 控制工作流卡片的展开与隐藏。
- 架构意义 ：将视觉尺寸计算与媒体查询从 SmartQA.vue 中抽离，使根组件保持干净。
### 4. useMessageParser.ts (数据清洗)
- 职责 ：解析大模型返回的复杂数据结构，将原始响应提取为前端可用的模块化数据。
- 功能点 ：
  - 从 content 中剥离 <think> 标签、Markdown 元数据。
  - 组装 Message 对象供视图层渲染。
- 架构意义 ：大模型输出往往是不可预测且混杂的字符串，这个 hook 是整个系统的数据“过滤器 (Sanitizer)”。
### 5. useMarkdown.ts (渲染引擎适配器)
- 职责 ：前端 Markdown 解析与代码高亮的核心基座。
- 功能点 ：
  - 封装 marked 解析器并自定义 Renderer（如代码块、XSS 防御）。
  - 集成 shiki 进行代码语法高亮（通过异步单例加载，不阻塞首屏）。
  - 集成 katex 进行数学公式渲染。
- 架构意义 ：将庞大且 CPU 密集的 AST 词法分析过程抽离，使得任何组件（如 ChatCard 、 ThinkingBlock ）都能 O(1) 获取安全的 HTML 结果。
### 6. useChart.ts (图表适配器)
- 职责 ：专门负责将大模型吐出的 JSON/JSON5 配置映射为前端图表库（如 ECharts）的 Option 结构。
- 功能点 ：
  - 处理大模型生成图表配置时的容错与回退机制。
- 架构意义 ：实现了文本到可视化的转译，隔离了 AI 输出格式与图表组件。
### 总结
这是一个非常标准且成熟的 "Hook-Driven Architecture" ：

- useChatSession + modes/* ： 网络与状态流转 (Core)
- useAgentSelection + useAttachments ： 用户输入准备 (Input)
- useMarkdown + useChart + useMessageParser ： 数据解析与渲染引擎 (Output)
- useSmartQALayout ： 视图编排 (Layout)