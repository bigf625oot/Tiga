智能体中心的todo list
1.智能体中心列表的增删改查
2.智能体的筛选功能
3.智能体的搜索功能
4.智能体配置功能包含：
4.1 智能体的基本信息配置
基座模型支持非嵌入模型以外的模型
4.2 智能体的系统提示词配置
4.3 智能体的用户脚本配置
4.4 智能体的推理模式配置
5.知识库的获取以及勾选功能
6.智能体的工具箱中的工具配置，Agno框架默认的工具包含：
6.1 YFinance: 获取股票价格、财务报表、分析师建议（免费）。
OpenBB: 开源金融终端数据。
Financial Datasets: 专门的财报和 SEC 文件检索。
6.2 PythonTools: 让 Agent 在本地环境执行 Python 代码。
ShellTools: 执行终端命令（慎用）。
FileTools: 读写本地文件系统。
GitHub: 自动化管理仓库、Issue、PR 和代码搜索。
Docker: 管理容器和镜像。
6.3 SQL (Postgres, MySQL, SQLite): 直接运行 SQL 查询。
DuckDB: 本地高性能分析型数据库。
Pandas: 处理大型 CSV 或 Excel 数据表。
6.4 DALL-E / Replicate / Fal.ai: 图像生成。
Firecrawl / BeautifulSoup: 网页抓取与解析。
6.5 Reasoning Tools: 提供“思考”过程的工具，支持思维链（CoT）。
MCP (Model Context Protocol): 最重要的内置功能之一，支持连接到任何符合 MCP 标准的外部服务器，理论上可以接入无限的第三方插件。