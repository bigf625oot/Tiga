"""
定义 Operations Team 的具体实现
"""

from typing import List, Dict, Optional
from agno.agent import Agent as AgnoAgent
from sqlalchemy.ext.asyncio import AsyncSession
from .base_team import BaseTeam

class OperationsTeam(BaseTeam):
    """
    A team for executing operational tasks (DevOps, Data Entry, etc.).
    
    Structure:
    - Leader: Operations Manager
    - Member 1: Shell Executor (Runs commands)
    - Member 2: File Manager (Handles files)
    - Member 3: Cloud Specialist (Optional, AWS/Azure tools)
    """
    
    async def initialize(self, 
                         manager_id: str,
                         shell_agent_id: str, 
                         file_agent_id: str,
                         cloud_agent_id: str = None) -> AgnoAgent:
        
        # 1. Build Members
        shell_agent = await self._build_member_agent(shell_agent_id)
        file_agent = await self._build_member_agent(file_agent_id)
        
        team_members = [shell_agent, file_agent]
        
        if cloud_agent_id:
            cloud_agent = await self._build_member_agent(cloud_agent_id)
            team_members.append(cloud_agent)
            
        self.members = team_members

        # 2. Build Manager
        from app.services.eah_agent.agent.builder import AgentBuilder
        
        builder = AgentBuilder(self.db, manager_id)
        await builder._fetch_agent_config()
        await builder._fetch_model_config()
        await builder._load_tools()
        
        # 3. Instructions
        role_descriptions = "\n".join([f"- {m.name}: {m.description or 'No description'}" for m in team_members])
        
        team_instructions = f"""
## Operations Management
You are the Operations Manager. Your team consists of:
{role_descriptions}

Your goal is to execute user requests safely and efficiently.
1. Break down complex requests into steps (e.g. "Write script" -> "Execute script").
2. Assign file operations to the File Manager.
3. Assign command execution to the Shell Executor.
4. Verify results before confirming completion.

SAFETY WARNING: Double check all commands before delegation.
"""
        builder.instruction_builder.instructions += "\n" + team_instructions
        
        # 4. Construct Leader
        from app.services.llm.factory import ModelFactory
        
        model = ModelFactory.create_model(builder.llm_model)
        final_instructions = builder.instruction_builder.build()
        
        self.team_agent = AgnoAgent(
            name=builder.agent_model.name,
            model=model,
            team=team_members,
            instructions=final_instructions,
            tools=builder.tools,
            # show_tool_calls=True,
            markdown=True,
            debug_mode=True
        )
        
        return self.team_agent
