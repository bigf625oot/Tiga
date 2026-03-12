from typing import List, Optional, Any
from agno.agent import Agent as AgnoAgent
from .base_team import BaseTeam
from app.services.eah_agent.agent.builder import AgentBuilder
from app.services.llm.factory import ModelFactory

class DynamicTeam(BaseTeam):
    """
    动态团队类：支持通过配置（JSON/Dict）在运行时构建团队。
    支持四种模式：
    1. Coordinate (协调模式): 默认模式，Leader 分析协调。
    2. Route (路由模式): Leader 决策并分发给一个最佳成员。
    3. Broadcast (广播模式): Leader 广播给所有成员并汇总。
    4. Tasks (任务模式): Leader 拆解任务列表，成员自主认领或分配。
    """

    async def initialize(self, **kwargs) -> AgnoAgent:
        """
        根据传入的配置初始化动态团队。
        
        Args:
            leader_id (str): 担任领导者的 Agent ID。
            member_ids (List[str]): 团队成员的 Agent ID 列表。
            mode (str, optional): 团队模式 (coordinate, route, broadcast, tasks). 默认为 coordinate.
            instructions (str, optional): 针对该团队任务的特定自定义指令。
        """
        leader_id = kwargs.get("leader_id")
        member_ids = kwargs.get("member_ids", [])
        mode = kwargs.get("mode", "coordinate").lower()
        custom_instructions = kwargs.get("instructions")

        if not leader_id:
            raise ValueError("DynamicTeam requires a 'leader_id' in configuration")

        # 1. 动态构建所有成员 Agent
        self.members = []
        for agent_id in member_ids:
            member = await self._build_member_agent(agent_id)
            self.members.append(member)

        # 2. 准备领导者 (Leader) 配置
        builder = AgentBuilder(self.db, leader_id)
        await builder._fetch_agent_config()
        await builder._fetch_model_config()
        await builder._load_tools()
        builder._configure_instructions()

        # 3. 根据模式生成团队协作 Prompt
        role_descriptions = "\n".join([
            f"- {m.name}: {m.description or 'Specialized assistant'}" 
            for m in self.members
        ])
        
        team_coordination_prompt = ""
        
        if mode == "coordinate":
            team_coordination_prompt = f"""
## Team Mode: Coordinate
You are the Research Coordinator. You have a team of specialized agents:
{role_descriptions}

Your goal is to coordinate these agents to fulfill the user's request:
1. Analyze the request and determine which members are best suited for sub-tasks.
2. Delegate tasks to one or more members as needed.
3. Synthesize their outputs into a final coherent response.
4. Only use your own tools when necessary to bridge gaps.
"""
        elif mode == "route":
            team_coordination_prompt = f"""
## Team Mode: Route
You are a Gateway Router. You have a team of specialized agents:
{role_descriptions}

Your goal is to route the user's request to the SINGLE best-suited agent.
1. Analyze the user's intent.
2. Choose EXACTLY ONE member that matches the intent best.
3. Delegate the full request to that member.
4. Return that member's response directly to the user without modification.
Do NOT attempt to answer the question yourself if a member can do it.
"""
        elif mode == "broadcast":
            team_coordination_prompt = f"""
## Team Mode: Broadcast
You are a Broadcaster. You have a team of agents:
{role_descriptions}

Your goal is to get opinions/results from ALL members.
1. Send the user's request to EVERY member in the team.
2. Collect all their responses.
3. Synthesize and compare their answers into a comprehensive summary.
"""
        elif mode == "tasks":
            team_coordination_prompt = f"""
## Team Mode: Task Manager
You are a Task Manager. You have a team of workers:
{role_descriptions}

Your goal is to execute a complex multi-step workflow:
1. Break down the user's request into a checklist of specific, actionable sub-tasks.
2. For each sub-task, assign it to the most appropriate member.
3. Track progress and ensure all tasks are completed.
4. Compile the final result once all tasks are done.
"""
        else:
            # Default fallback
            team_coordination_prompt = f"""
## Team Coordination
You are the Team Leader. Team members:
{role_descriptions}
Please coordinate them to answer the user request.
"""

        # 将协作逻辑添加到领导者的指令中
        builder.instruction_builder.instructions += "\n" + team_coordination_prompt
        
        # 如果配置中传入了额外的自定义指令，也一并注入
        if custom_instructions:
            builder.instruction_builder.instructions += f"\n\n## Specific Instructions\n{custom_instructions}"

        # 4. 实例化领导者 AgnoAgent
        model = ModelFactory.create_model(builder.llm_model)
        is_reasoning = ModelFactory.should_use_agno_reasoning(builder.llm_model)
        model_config = getattr(builder.agent_model, "model_config", {}) or {}
        show_tool_calls = model_config.get("show_tool_calls", True)

        self.team_agent = AgnoAgent(
            name=builder.agent_model.name,
            model=model,
            team=self.members,        # 注入成员
            instructions=builder.instruction_builder.build(),
            tools=builder.tools,
            show_tool_calls=show_tool_calls,
            markdown=True,
            reasoning=is_reasoning,
            debug_mode=True
        )
        
        return self.team_agent
