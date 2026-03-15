4种核心模式：
1. 快问快答： Basic Agent  大模型支持输出 ，属于闲聊、知识问答、简答总结
1.1 对应服务： Basic Agent
1.2 侧重于直接的对话交互
1.3 代码demo：
agent = Agent(model=OpenAIChat(id="gpt-4o"), markdown=True)
-------------------------------------------------------------------
1. solo自规划： Agent+tools  ReAct 模式，Agent 可以根据用户指令和工具调用结果，自主规划和执行任务。比如根据用户指令，调用搜索引擎获取信息，然后根据信息生成回答。
对应服务： Autonomous Agent / Agent with Tools
实现方式： 为 Agent 配置 tools（工具库）并开启 show_tool_calls。
特点： 这是 Agno 的核心优势。当用户给出一个复杂目标时，Agent 会利用 ReAct 逻辑（推理-行动），自行决定调用哪个工具、如何处理返回结果，直到完成任务。
agent = Agent(
    tools=[DuckDuckGo(), YFinanceTools()], 
    show_tool_calls=True,
    instructions=["使用搜索工具寻找信息", "使用金融工具分析数据"]
)
------------------------------------------------------------------------
1. workflow： Agno的workflow类，基于状态机/流程图（DAG），可以定义多个 Agent 之间的协作关系，每个 Agent 负责不同的子任务。
对应服务： Agno Workflow
实现方式： 继承 Workflow 类，定义结构化的步骤（Steps）。
特点： 对应 “有状态的顺序/条件执行”。与 Agent 的随机应变不同，Workflow 强调确定性的流程控制（如：第一步做 A，第二步根据 A 的结果决定做 B 还是 C）。它适合处理长时任务或需要严格合规的业务流程。
class MyWorkflow(Workflow):
    def run(self, topic):
        # 步骤1：搜索
        # 步骤2：总结
        # 步骤3：写入数据库

2. Team模式：基于Agno的Agent Team 类，可以定义多个 Agent 组成一个团队，每个 Agent 负责不同的子任务。团队成员之间可以协作，共享信息和资源。
对应服务： Agent Team (Multi-Agent Orchestration)
实现方式： 在一个主 Agent 的 team 参数中传入多个子 Agent。
特点： 对应 “层级化管理”。主 Agent 相当于“领班”或“经理”，它接收到任务后，会根据子 Agent 的描述（Description），将任务分发给不同的“专家”执行，最后汇总结果。
agent_team = Agent(
    team=[web_agent, finance_agent, writer_agent],
    instructions=["协调团队成员完成一份综合行业报告"],
    show_tool_calls=True
)
