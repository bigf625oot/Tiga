# Findings

## Pathway ETL 现状
- `app/models/pathway.py` 实际是运行引擎实现（PathwayEngine），并且顶层依赖 `pathway` 第三方包。
- CRUD/路由/适配器曾错误从 `app.models.pathway` 导入 DB 模型符号，导致启动 ImportError。
- 已新增 `app/models/pathway_db.py` 承载 DB 模型与枚举，并将相关导入切换到该模块。

