建议的目录结构
eah_agent/
├── core/                # 核心引擎 (NLU, Dispatcher, Base Classes)
├── handlers/            # 【原 agents 文件夹】四种模式的业务入口
│   ├── quick_handler.py # 处理快问快答
│   ├── plan_handler.py  # 处理自规划 
│   ├── team_handler.py  # 处理 Team 协作逻辑
│   └── flow_handler.py  # 处理 Workflow 逻辑
├── agent/               # 单体 Agent 的具体定义/配置
├── team/                # Team 的具体成员编排定义
├── workflows/           # Workflow 的具体步骤定义
├── domain/              # 领域模型 (Prompt, Schema)
├── tools/               # 原子工具
├── skills/              # 复合技能
└── ...

目录划分的逻辑：
1.core 负责“怎么转”（底层的驱动、意图识别）。
2.handlers 负责“怎么接”（四种模式的业务入口）。
3.agent/team/workflows 负责“是什么”（具体的 Agent 提示词、团队成员、流程步骤）。
4.tools/skills 负责“能做什么”（插件和业务函数）。

具体的工作计划：
1. 先完成 core 模块，确保意图识别和 dispatcher 正常工作。
2. 实现 handlers 模块，分别处理快问快答、自规划、Team 协作和 Workflow 逻辑。
3. 定义 agent/team/workflows 模块，包括具体的 Agent 提示词、团队成员和流程步骤。
4. 实现 tools/skills 模块，包括原子工具和复合技能。
5. 测试和调试，确保系统正常运行。

原则：
1. 保证已有功能的正常运行。
1. 保持模块之间的职责清晰，避免模块之间的循环依赖。
2. 每个模块都有其特定的功能，不要将不同功能的代码混杂在一起。
3. 及时进行代码 review，确保代码质量和可维护性。

改造接口契约：
1. 定义 Handler 协议：首先在 core 中定义 BaseHandler 接口，确保 Dispatcher 能够以多态方式调用不同的业务模式。
2. 统一流式协议：将 ChatService 中的 SSE 格式化和 DeepSeek 思考逻辑抽取到 core/stream_processor.py，作为全局唯一的输出格式转换器。
3. 配置驱动 Agent 创建：在 core/agent_manager.py 中实现工厂模式，根据 domain/ 中的配置文件（Prompt 模板、工具清单）动态构建 Agno 实例。
4. Skill/Tool 注册制：所有的 skills/ 和 tools/ 必须实现标准的注册接口，方便 Agent 动态加载。
5. 存量兼容：重构的第一步是建立新旧系统的桥接，通过 eah_agent.core.control_plane 作为新入口，保持原 ChatService 结构不变，内部逻辑逐步外包给新架构。