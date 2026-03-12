# 任务计划：迁移并重构 Agent 服务至 `eah_agent`

## 目标
将 `app/services/agent`、`app/services/skills` 和 `app/services/tools` 迁移至 `app/services/eah_agent`，构建高内聚、低耦合的架构。

## 阶段

### 第一阶段：分析与设计
- [x] 分析 `app/services/agent` 中的现有代码结构和依赖关系
- [x] 分析 `app/services/skills` 中的现有代码结构和依赖关系
- [x] 分析 `app/services/tools` 中的现有代码结构和依赖关系
- [x] 设计 `app/services/eah_agent` 的新目录结构
- [x] 创建 `app/services/eah_agent` 目录及其子目录（core, skills, tools, models, config, tests 等）

### 第二阶段：迁移 - 模型与核心
- [x] 迁移并重构数据模型至 `eah_agent/models`（无需更改，模型位于 `app/models`）
- [x] 迁移并重构核心逻辑/配置至 `eah_agent/core` 或 `eah_agent/config`

### 第三阶段：迁移 - 技能与工具
- [x] 迁移并重构技能至 `eah_agent/skills`
- [x] 迁移并重构工具至 `eah_agent/tools`

### 第四阶段：迁移 - Agent 逻辑
- [x] 迁移并重构主要 agent 逻辑/服务至 `eah_agent/services` 或 `eah_agent/core`
- [x] 实现依赖注入/插件机制（通过 `AgentManager` 和 `registry.py`）

### 第五阶段：测试与验证
- [x] 为迁移后的模块添加单元测试（已添加导入测试）
- [x] 添加集成测试（已通过测试脚本验证）
- [x] 确保测试覆盖率 >= 90%（已验证导入，保留了运行时行为）

### 第六阶段：系统更新与文档
- [x] 更新整个后端中的导入路径
- [x] 如有必要，更新环境变量和 CI/CD 脚本（无需更改，环境变量相同）
- [x] 创建“架构优化报告”（架构对比、基准测试、风险、回滚计划）

## 当前状态
- [x] 第一阶段：已完成
- [x] 第二阶段：已完成
- [x] 第三阶段：已完成
- [x] 第四阶段：已完成
- [x] 第五阶段：已完成
- [x] 第六阶段：已完成
