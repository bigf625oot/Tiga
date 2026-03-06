# QA 模块代码审查报告

## 1. 审查范围与方法
- 范围：`frontend/src/features/qa`（含 `components` 与 `components/__tests__`）
- 方法：逐文件静态审查 + 引用关系交叉检索 + 冗余逻辑对比
- 目标：输出用途清单、问题代码标记、可执行重构方案与回归检查清单

## 2. 文件用途清单

| 文件（相对 qa） | 主要功能与业务场景 | 对外暴露 API / 组件 | 被哪些模块引用 | 冗余/可替代性评估 |
|---|---|---|---|---|
| `components/SmartQA.vue` | QA 主容器，负责会话、SSE 流式、模式切换、附件上传与右侧任务联动 | 默认导出组件；事件 `refresh-sessions` | `src/App.vue`、`components/__tests__/SmartQA.spec.js`、`components/__tests__/SmartQA.sse.spec.js` | 存在较大模板重复块，建议拆分输入区与模式面板 |
| `components/MessageList.vue` | 对消息按角色/时间分组并滚动管理 | 默认导出组件；`defineExpose({ scrollToBottom })` | `components/SmartQA.vue`、`components/__tests__/MessageList.spec.js` | 无明显冗余，职责清晰 |
| `components/ChatCard.vue` | 渲染知识问答/智能查询消息（Markdown、图表、引用） | 默认导出组件；事件 `locate-node` | `components/MessageList.vue`、`components/ChatCard.spec.js` | 与 `MessageItem.vue` 职责重叠，建议收敛 |
| `components/MessageItem.vue` | 复杂消息渲染（think、文档卡片、来源面板） | 默认导出组件；事件 `locate-node/show-doc-summary/open-doc-space` | `components/__tests__/MessageItem.spec.js` | 仅被测试引用，属于候选死代码 |
| `components/SourcePanel.vue` | 展示文档来源/片段并支持定位 | 默认导出组件；事件 `locate-node/show-doc-summary` | `components/MessageItem.vue`、`components/__tests__/SourcePanel.spec.js` | 受 `MessageItem.vue` 生存状态影响 |
| `components/DocCard.vue` | 文档卡片展示与跳转 | 默认导出组件；事件 `click` | `components/MessageItem.vue` | 与 `FileCard.vue` 结构高度相似，可合并 |
| `components/FileCard.vue` | 文件卡片展示与点击事件 | 默认导出组件；事件 `click` | `components/MessageItem.vue` | 与 `DocCard.vue` 结构高度相似，可合并 |
| `components/ReferencesTable.vue` | 参考来源表格视图（排序/分页） | 默认导出组件 | `components/SmartQA.vue`（仅 import，未渲染） | 闲置实现，候选下线 |
| `components/ReferencesCards.vue` | 参考来源卡片视图（网格展示） | 默认导出组件 | `components/SmartQA.vue`（仅 import，未渲染） | 闲置实现，候选下线 |
| `components/AutoTaskPanel.vue` | 自动任务工作台容器（host/task/node） | 默认导出组件；事件 `close/run-task` | `components/SmartQA.vue`、`components/__tests__/AutoTaskPanel.spec.ts` | 无明显冗余，业务核心 |
| `components/TaskManagement.vue` | 任务统计、模板创建、活动时间线 | 默认导出组件；事件 `create-task/refresh-activities/run-task` | `components/AutoTaskPanel.vue` | 存在调试日志残留 |
| `components/NodeList.vue` | 节点列表、刷新、命令触发 | 默认导出组件；事件 `refresh/run-command/select` | `components/AutoTaskPanel.vue` | 无明显冗余 |
| `components/NodeDetail.vue` | 单节点详情、指标与告警面板 | 默认导出组件；事件 `back` | `components/AutoTaskPanel.vue` | 指标与告警目前为 mock，需替换真实接口 |
| `components/GatewayInfo.vue` | 网关信息与连接状态查看 | 默认导出组件 | `components/AutoTaskPanel.vue` | 展示敏感字段，需加强权限控制 |
| `components/TemplateCard.vue` | 自动任务模板卡片 | 默认导出组件；事件 `fill` | `components/TaskManagement.vue` | 无明显冗余 |
| `components/StatCard.vue` | 统计指标卡片 | 默认导出组件 | `components/TaskManagement.vue` | 无明显冗余 |
| `components/ChatCard.spec.js` | ChatCard 渲染测试 | 测试文件 | 无直接引用（测试入口加载） | 正常 |
| `components/__tests__/AutoTaskPanel.spec.ts` | AutoTaskPanel 行为测试 | 测试文件 | 无直接引用（测试入口加载） | 正常 |
| `components/__tests__/MessageItem.spec.js` | MessageItem think 标签测试 | 测试文件 | 无直接引用（测试入口加载） | 若删除 `MessageItem.vue` 需迁移或下线 |
| `components/__tests__/MessageList.spec.js` | MessageList 分组测试 | 测试文件 | 无直接引用（测试入口加载） | 已对齐当前 `.chat-card` 渲染结构 |
| `components/__tests__/SmartQA.spec.js` | SmartQA 会话切换测试 | 测试文件 | 无直接引用（测试入口加载） | 正常 |
| `components/__tests__/SmartQA.sse.spec.js` | SmartQA SSE 流式测试 | 测试文件 | 无直接引用（测试入口加载） | 已修复重复导入 `vi` 问题 |
| `components/__tests__/SourcePanel.spec.js` | SourcePanel 模式与事件测试 | 测试文件 | 无直接引用（测试入口加载） | 正常 |

## 3. 问题代码标记

### 3.1 Dead Code（完全未被生产链引用）
- `components/MessageItem.vue`：仅被 `components/__tests__/MessageItem.spec.js` 引用，生产链未进入
- `components/SourcePanel.vue`、`components/DocCard.vue`、`components/FileCard.vue`：仅被 `MessageItem.vue` 依赖，属于“间接候选死代码”

### 3.2 90%+ 重复逻辑
- `components/DocCard.vue` 与 `components/FileCard.vue`
  - 结构、交互和样式骨架高度一致（卡片容器、图标区、标题区、尾部箭头、点击抛出）
  - 建议合并为 `ResourceCard.vue`（通过 `kind/icon/title/subtitle/payload` 参数化）

### 3.3 空文件/仅注释/调试残留
- 空文件/仅注释文件：未发现
- 调试残留：
  - `components/SmartQA.vue` 中 `console.log("View doc summary:", item);`
  - `components/TaskManagement.vue` 中 `console.log("Activity clicked", act);`
  - 多处 `console.error(...)` 可保留为错误日志，但建议统一日志层

### 3.4 命名冲突或职责重叠
- `ChatCard.vue` 与 `MessageItem.vue`：均承担“助手消息渲染内核”职责，存在能力分叉风险
- `ReferencesTable.vue` 与 `ReferencesCards.vue`：同领域双实现，且当前均未实际渲染

## 4. 可执行重构方案

### 4.1 可删除文件（建议）
1. `components/ReferencesTable.vue`
   - 理由：在 `SmartQA.vue` 仅 import 未使用
2. `components/ReferencesCards.vue`
   - 理由：在 `SmartQA.vue` 仅 import 未使用
3. `components/MessageItem.vue`（第二阶段）
4. `components/SourcePanel.vue`、`components/DocCard.vue`、`components/FileCard.vue`（随第 3 项联动）
   - 理由：仅服务于 `MessageItem.vue`，主链已使用 `MessageList -> ChatCard`

### 4.2 需合并文件（建议）
- 合并源文件：
  - `components/DocCard.vue`
  - `components/FileCard.vue`
- 合并后目标文件：
  - `components/ResourceCard.vue`
- 合并步骤：
  1. 抽离共同模板（容器、左侧图标、标题、副标题、尾部箭头）
  2. 以 `kind` 或 `variant` 参数区分文档/文件样式与图标
  3. 统一事件为 `click(payload)`，由调用方决定处理逻辑
  4. 替换 `MessageItem.vue` 中对应引用（若保留 MessageItem）

### 4.3 删除/合并后需同步更新 import 清单
- 删除 `ReferencesTable/ReferencesCards` 后：
  - `components/SmartQA.vue`：
    - 删除 `import ReferencesTable from './ReferencesTable.vue'`
    - 删除 `import ReferencesCards from './ReferencesCards.vue'`
- 删除 `MessageItem` 链后：
  - `components/__tests__/MessageItem.spec.js`：迁移到 `ChatCard` 或删除
  - `components/__tests__/SourcePanel.spec.js`：若 `SourcePanel` 下线则删除或迁移
- 合并 `DocCard/FileCard -> ResourceCard` 后：
  - `components/MessageItem.vue`：
    - `import DocCard` / `import FileCard` 改为 `import ResourceCard`

## 5. 已执行变更（本次交付）
- 已为 `qa` 目录下全部现存文件补充标准化中文注释头
- 已修复 `components/__tests__/SmartQA.sse.spec.js` 的重复 `vi` 导入问题
- 已修复 `components/__tests__/MessageList.spec.js` 的过期选择器断言
- 已执行 QA 目录 7 个测试文件回归，结果为 21/21 通过（含现有 warning）
