# 全局任务中心开发任务与计划文档

## 1. 需求分析与背景
目标：实现一个全局任务中心功能，用于在后台处理耗时的异步任务（如大文件解析、分块上传、数据导出），并允许用户在任何页面查看进度。

**注意：** 需求描述中提到了 React 技术栈（shadcn/ui, Zustand, Lucide React, layout.tsx），但经过代码库审查，当前项目为 **Vue 3 + Vite** 项目。为了保证项目技术栈一致性，本计划将采用对应的 Vue 生态替代方案来实现完全相同的功能和设计。

## 2. 技术栈映射与选择
- **状态管理**：使用 **Pinia** 替代 Zustand（用于跨页面共享任务状态）
- **UI 库**：使用 **shadcn-vue**（基于 Radix Vue 和 Tailwind CSS）替代 shadcn/ui React
  - 需使用组件：`Button`, `Sheet`, `Progress`, `ScrollArea`, `Badge`
- **图标**：使用 **lucide-vue-next** 替代 Lucide React
- **动画**：使用 **Tailwind CSS**（包含 `animate-spin` 等）
- **全局集成**：在 **`App.vue`**（或项目的根 Layout 组件）中引入，替代 `layout.tsx`

## 3. 详细任务拆解

### 任务 1：定义状态管理 Store (Pinia)
**文件位置**：`/frontend/src/store/useTaskStore.ts`
- 定义 `Task` 接口：`id`, `name`, `progress` (0-100), `status` ('pending' | 'processing' | 'success' | 'error'), `createdAt`。
- 定义 State：`tasks` 数组。
- 定义 Actions：
  - `addTask(task: Omit<Task, 'id' | 'createdAt'>)`
  - `updateTaskProgress(id: string, progress: number)`
  - `updateTaskStatus(id: string, status: Task['status'])`
  - `removeTask(id: string)`
  - `clearCompletedTasks()`

### 任务 2：创建或引入必要的 UI 组件
**文件位置**：`/frontend/src/components/ui/*`
- 检查并安装/创建所需的 shadcn-vue 组件：
  - `Button`
  - `Sheet` (侧边栏)
  - `Progress` (进度条)
  - `ScrollArea` (滚动区域)
  - `Badge` (未读标记)

### 任务 3：开发任务中心组件 (TaskCenter.vue)
**文件位置**：`/frontend/src/components/TaskCenter.vue`
- **悬浮按钮**：固定在屏幕右下角，圆形按钮，带图标（如 `ListTodo` 或 `Inbox`）。
- **未读标记**：当有 `status === 'processing'` 的任务时，在按钮右上角显示红色小圆点或数字 Badge。
- **侧边栏 (Sheet)**：点击悬浮按钮时，从右侧滑出 Sheet。
- **任务列表**：
  - 使用 `ScrollArea` 包装任务列表，防止任务过多撑爆页面。
  - 单个任务卡片展示：任务名称、百分比进度条（`Progress`）、状态图标。
  - 状态图标映射：
    - `processing`: 显示 `Loader2` 旋转图标 (`animate-spin`)。
    - `success`: 显示绿色勾选图标 (`CheckCircle2`)。
    - `error`: 显示红色感叹号图标 (`AlertCircle`)。
  - 附加操作：支持删除单个任务记录，并在顶部/底部提供“清除已完成”按钮。

### 任务 4：全局集成
**文件位置**：`/frontend/src/App.vue`
- 导入 `TaskCenter.vue` 组件。
- 将其放置在应用根节点中，确保在所有路由和页面下都可见并且状态保持一致。

## 4. 开发进度计划 (Todo)
- [ ] **Phase 1**: 编写本计划文档（已完成）
- [ ] **Phase 2**: 创建 Pinia Store (`useTaskStore.ts`) 并定义类型和方法
- [ ] **Phase 3**: 检查并补全缺少的 shadcn-vue UI 组件
- [ ] **Phase 4**: 实现 `TaskCenter.vue` 组件逻辑和样式
- [ ] **Phase 5**: 将 `TaskCenter.vue` 挂载到 `App.vue` 并进行测试
- [ ] **Phase 6**: （可选）编写测试用例验证全局状态共享是否正常工作