# QA 重构回归检查清单

## 单元测试
- [ ] `ChatCard.spec.js` 通过
- [ ] `MessageList.spec.js` 通过（必要时先修复过期断言）
- [ ] `SmartQA.spec.js` 通过
- [ ] `SmartQA.sse.spec.js` 通过
- [ ] `AutoTaskPanel.spec.ts` 通过
- [ ] `SourcePanel.spec.js` 通过（若组件保留）

## 组件测试
- [ ] SmartQA 三种模式切换（chat / workflow / auto_task）可用
- [ ] 消息流式输出中 think/text/sources 渲染正常
- [ ] 附件上传与知识库文档选择流程正常
- [ ] AutoTaskPanel 的 host/task/node 标签切换正常
- [ ] NodeList 到 NodeDetail 的选择与返回链路正常

## E2E 关键路径
- [ ] 创建新会话并发送消息，SSE 回复完整
- [ ] 切换会话后模式恢复为 chat，右侧面板状态符合预期
- [ ] auto_task 模式创建任务成功并可看到任务活动更新
- [ ] workflow 模式可触发任务规划并展示阶段消息
- [ ] 右侧工作区定位能力（locateNode/openDocSpace）可达

## 重构专项验证（删除/合并后执行）
- [ ] 删除 `ReferencesTable/ReferencesCards` 后构建通过
- [ ] 删除 `MessageItem` 链后主链消息渲染无回归
- [ ] 合并 `DocCard/FileCard` 后点击事件 payload 与旧行为一致
- [ ] 全仓 `qa` 相关 import 无失效路径
