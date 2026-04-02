1.消息聊天分为三大模式：Lite, Agentic, Specialized

1.2  Agentic 模式：
- 用户输入：文本、多附件、语音、多模态输入
- 模型输出：
- - 过程（thought）过程（thought） ：多级思考，包括问题分解、问题解决、问题总结（planning）、自我修正（selfrection）、反思（reflection）、多模型博弈（multi-Agent）等
- - 执行工具（tool） ：根据用户输入调用外部工具，如网络搜索、知识库片段检索、翻译、计算器、终端执行（shell）\文件系统、沙箱代码、API集成等等
- - 内容生成（content） ：根据用户输入和模型输出，生成最终的长文本内容、代码、网页等
- - 格式化输出产物（format） ：使用Agno自带的格式化功能，将内容转换为markdown格式包含文档引用、图片、表格、代码块、数学公式、图表、链接、列表模型。输出内容包含文档引用、图片、表格、代码块、数学公式、图表、链接、列表等，还包含thought (思考)、 plan_step (规划步骤)、 tool (工具调用)、 web_search (网络搜索)、 kb_retrieval (知识库片段) 以及最终的 content (markdown或者使用工具输出的docx、pdf、PPT、html格式等)

1.3  Specialized 模式：用户输入复杂，模型输出内容包含数据集、库表、知识库引用、图表、链接、列表等，还包含thought (思考)、 plan_step (规划步骤)、 tool (工具调用)、图表 (chart)等




2. Agentic模式模式：视觉加法（More is more）
- Thought Process: 阶梯式展示。例如：1. 需求分析 -> 2. 文件检索 -> 3. 代码编写 -> 4. 运行自检。
- Used Tool: 详细记录每一个 FS (文件系统) 操作。例如：read_file -> edit_file -> run_test。
- File Diff (核心): 采用对比视图。绿色代表新增，红色代表删除（如图中 Card.vue 的变更）。支持手动修改 Diff 代码。
- Terminal: 实时滚动。显示 npm run lint 或 jest 测试结果，让用户看到 AI 的“验证过程”。
- Action Buttons: 增加 Apply All (应用全部修改)、Step Over (单步执行)、Fix with AI (报错后自动修复)。

闭环操作：
1. Human-in-the-Loop (人工干预):在 Agentic 模式下，当 AI 准备执行“高危操作”（如删除文件、发送邮件、支付）时，在 UI 中强制中断并弹出 Approval Required (请求授权) 按钮。
2. Context Management (上下文感知):
- Lite: 仅感知当前对话。
- Agentic: 感知整个工程目录（src/ 下的所有文件）。
- Specialized: 感知整个知识库的索引结构。
3. State Rollback (状态回滚):
在图片下方的 Discard 旁边增加 Undo。如果 AI 修改代码导致编译失败，用户可以一键回滚到上一个稳定版本。
4. Token/Cost Monitor (成本监控):
针对 Specialized/Agentic 模式（消耗 Token 较多），在顶部显示当前任务的消耗进度。

共用UI
1. 共用底层协议： 无论哪种模式，底层都走 Thought -> Tool -> Result 的循环。
2. 共用 UI 框架： 采用**“模块化容器”**设计。
3. Top Section: 状态与逻辑 (Thought/Planning)
4. Middle Section: 核心产物 (Code Diff / Markdown / Data Table)
5. Bottom Section: 环境反馈 (Terminal / Logs)
6. Footer: 决策交互 (Apply / Discard / Regenerate)