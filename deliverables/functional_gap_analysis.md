# 功能差距清单与优先级 (Functional Gap Analysis)

| 优先级 (Priority) | 功能模块 (Module) | 后端能力 (Backend Capability) | 前端需求 (Frontend Requirement) | 差距描述 (Gap Description) |
| :--- | :--- | :--- | :--- | :--- |
| **P0 (Critical)** | **核心画布 (Canvas)** | `pw.run()` (Stream Execution) | 画布与节点渲染 | 需要实现拖拽式画布，支持节点连接、删除、移动。 |
| **P0** | **数据源 (Source)** | `pw.io.kafka.read` | Kafka 配置面板 | 缺少 Kafka 连接配置表单（Brokers, Topics, GroupID, Format）。 |
| **P0** | **数据源 (Source)** | `pw.io.fs.read` (S3/Local) | 文件源配置面板 | 缺少 S3/本地文件路径选择与格式配置。 |
| **P0** | **数据源 (Source)** | `GenericSQLSource` | SQL 编辑器 | 缺少 SQL 查询输入框与数据库连接配置。 |
| **P0** | **转换 (Transform)** | `cleaning` (Text/Data ops) | 算子配置面板 | 缺少通用清洗算子的参数配置（如正则表达式、替换值、目标列）。 |
| **P0** | **转换 (Transform)** | `UDF` (User Defined Functions) | 代码编辑器 | 缺少 Python 代码编辑器或文件上传组件，用于编写自定义逻辑。 |
| **P0** | **接收器 (Sink)** | `ClickHouseSink`, `PostgresSink` | 数据库输出配置 | 缺少目标数据库的连接与表映射配置。 |
| **P0** | **执行控制 (Execution)** | `Job Management` API | 运行/停止按钮 | 前端需调用 API 启动/停止任务，并显示当前状态。 |
| **P1 (High)** | **调试 (Debug)** | `pw.debug.compute_and_print` | 数据预览 | 需要在节点上右键“预览数据”，后端需支持采样返回。 |
| **P1** | **监控 (Monitor)** | `Prometheus Metrics` | 实时指标看板 | 画布上方需显示处理速率（eps）、延迟等核心指标。 |
| **P1** | **错误处理 (Error)** | `Exceptions` | 错误提示与高亮 | 运行失败时，需解析后端日志并高亮出错节点。 |
| **P2 (Medium)** | **转换 (Transform)** | `Windowing` / `GroupBy` | 窗口聚合配置 | 复杂的流式窗口聚合配置界面（滑动窗口、跳跃窗口）。 |
| **P2** | **元数据 (Metadata)** | `Lineage` | 血缘图谱 | 自动生成字段级血缘展示。 |
| **P3 (Low)** | **辅助功能 (Aux)** | N/A | 模板库 | 预置常用 ETL 模板（如 "Kafka to ClickHouse"）。 |
