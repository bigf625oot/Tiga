# UI 实现规范 (Design Specifications)

## 1. 基础规范 (Tokens)

### 字体 (Typography)
- **Font Family**: `Inter`, system-ui, sans-serif
- **Scale**:
  - **H1**: 24px/32px Semibold (页面标题)
  - **H2**: 18px/28px Semibold (区块标题)
  - **H3**: 16px/24px Medium (组件标题)
  - **Body**: 14px/20px Regular (正文)
  - **Small**: 12px/16px Regular (辅助信息)
  - **Code**: `JetBrains Mono`, monospace (代码编辑器)

### 色彩 (Colors) - Tailwind Slate
- **Primary**: `slate-900` (#0f172a) / Dark: `slate-50`
- **Secondary**: `slate-100` (#f1f5f9) / Dark: `slate-800`
- **Accent**: `indigo-600` (#4f46e5) (选中、运行状态)
- **Destructive**: `red-500` (#ef4444) (错误、删除)
- **Success**: `emerald-500` (#10b981) (运行成功)
- **Warning**: `amber-500` (#f59e0b) (警告)
- **Background**: `slate-50` (#f8fafc) (画布背景)
- **Surface**: `white` (#ffffff) (卡片、面板)
- **Border**: `slate-200` (#e2e8f0)

### 间距 (Spacing)
- **Grid**: 4px base
- **Component Gap**: 8px (space-x-2, space-y-2)
- **Section Gap**: 24px (space-y-6)
- **Padding**: 16px (p-4)

### 圆角 (Radius)
- **Canvas Node**: 12px (rounded-xl)
- **Card**: 8px (rounded-lg)
- **Button**: 6px (rounded-md)
- **Input**: 4px (rounded)

### 阴影 (Shadows)
- **Card**: `shadow-sm`
- **Hover**: `shadow-md`
- **Drag**: `shadow-lg`

## 2. 核心组件设计

### 1. 画布 (Canvas)
- **背景**: `bg-slate-50` + Dot Pattern (`text-slate-200`)
- **Grid**: 20px
- **缩放**: Min 10%, Max 200%
- **MiniMap**: 右下角，半透明

### 2. 节点 (Node)
- **尺寸**: 宽度固定 240px，高度自适应
- **结构**:
  - **Header**: 图标 + 标题 + 状态指示器
  - **Body**: 关键配置摘要 (最多3行)
  - **Handles**: 左侧输入 (Target)，右侧输出 (Source)
- **状态样式**:
  - **Default**: `border-slate-200 bg-white`
  - **Selected**: `ring-2 ring-indigo-500 border-indigo-500`
  - **Error**: `border-red-500 bg-red-50`

### 3. 左侧组件库 (Sidebar)
- **宽度**: 240px
- **布局**: Accordion 分类 (Sources, Transforms, Sinks)
- **Item**: 图标 + 文本，支持 `draggable`

### 4. 右侧属性面板 (Property Panel)
- **宽度**: 320px
- **头部**: 节点名称 (可编辑) + ID
- **内容**:基于 Schema 生成的表单 (AutoForm)
  - Input, Select, Switch, CodeEditor
- **底部**: "应用" / "重置" 按钮

### 5. 底部调试栏 (Bottom Panel)
- **高度**: 可折叠 (Header 40px, Content 200px)
- **Tabs**: 日志 (Logs) | 数据预览 (Data) | 指标 (Metrics)
