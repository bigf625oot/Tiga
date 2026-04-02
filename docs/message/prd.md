Trae 风格多模态智能体交互系统
1. 核心架构：基于块（Block-Based）的协议
消息不再是单一的字符串，而是一个由不同功能的“块”组成的有序数组。这种结构允许 AI 在一次回复中交替进行思考、调用工具、修改代码和输出文本。
1.1 基础数据模型 (TypeScript)
code
TypeScript
// 消息流状态
type StreamStatus = 'streaming' | 'completed' | 'error';

// 块类型枚举
type BlockType = 'thought' | 'text' | 'tool_call' | 'tool_result' | 'action' | 'plan' | 'terminal' | 'search' | 'visualization' | 'confirmation';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  status: StreamStatus;
  blocks: ContentBlock[]; // 有序块数组
}
2. 详细块协议规范 (JSON Schema)
2.1 逻辑类块
Thought (思考): type: "thought", content: string, state: "thinking" | "collapsed" | "expanded".
Plan (计划): type: "plan", steps: Array<{id: string, text: string, status: "pending" | "running" | "completed"}>.
2.2 执行类块
Tool Call (工具调用): type: "tool_call", call_id: string, tool_name: string, arguments: object, state: "running" | "success" | "error".
Tool Result (结果): type: "tool_result", call_id: string, content: string, is_error: boolean.
Terminal (终端): type: "terminal", command: string, output: string, status: "running" | "success" | "error".
2.3 Trae 核心动作块
Action (文件操作):
action_type: "create_file" | "edit_file" | "delete_file"
path: string, description: string
diff: string (Unified Diff 格式)
status: "pending" | "applied" | "rejected"
2.4 增强交互块
Search (搜索): query: string, sources: Array<{title: string, url: string, favicon: string}>.
Confirmation (确认): message: string, context_id: string.
Visualization (可视化): vis_type: "mermaid" | "recharts", data: string.
3. UI/UX 渲染需求 (Trae 视觉规范)
3.1 统一卡片样式
容器: 圆角 12px，边框 1px solid var(--border-color)，背景 var(--card-bg)。
阴影: 微弱阴影 0 2px 8px rgba(0,0,0,0.05)。
间距: 块与块之间垂直间距 12px。
3.2 关键组件行为
Thought 组件:
样式：浅灰色背景，左侧 2px 装饰条。
行为：流式输出时默认展开，完成后延迟 2s 自动折叠（Accordion 效果）。
Action 卡片 (核心):
顶部：文件名 + 操作类型标签（绿色 New, 蓝色 Edit）。
中部：高度限制在 300px 内的 Diff 查看器，带滚动条。
底部：Discard 和 Apply 按钮。点击 Apply 后卡片变为置灰锁定状态。
Terminal 组件:
样式：深色背景（Jet Black），Monospace 字体，模拟光标闪烁。
Plan 组件:
样式：带 Checkbox 的垂直步骤条，当前步骤带呼吸灯动效。
4. 流式传输与状态管理逻辑
4.1 增量更新逻辑 (Delta Processing)
前端必须支持按 block_index 更新：
若收到新 block_index，在 blocks 数组中 push 新块。
若收到已有 block_index 且包含 delta，将 delta.content 拼接至对应块。
自动滚动: 仅当用户处于滚动条底部时，开启跟随滚动。
4.2 状态联动
当 tool_result 到达时，需根据 call_id 自动定位到对应的 tool_call 块，并将其 state 从 running 修改为 success。
5. 执行指令 (交给 Trae 的任务分解)
请按以下步骤分步实现：
Step 1: 类型定义 - 在 src/types/chat.ts 中实现上述所有接口。
Step 2: Mock 数据生成 - 编写一个 mockMessage 常量，包含 thought -> tool_call -> tool_result -> action -> text 的全流程数据。
Step 3: 核心分发器 - 编写 MessageRenderer.tsx，通过 switch-case 根据 block.type 渲染不同子组件。
Step 4: 关键 UI 实现 -
实现 ActionCard (需支持 Diff 高亮)。
实现 ThoughtAccordion (需支持流式展开动画)。
实现 ToolStatusCard (需支持 Loading 状态)。
Step 5: 样式打磨 - 使用 Tailwind CSS 适配深色/浅色模式，确保视觉精致感符合 Trae 标准。
补充提示：
请优先使用 Lucide-React 图标库。
代码高亮推荐使用 react-syntax-highlighter。
Diff 渲染可使用 react-diff-view 或自定义简单的行高亮逻辑。
