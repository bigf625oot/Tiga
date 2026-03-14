"""
定义 Research Team 的具体实现
"""

from typing import List, Dict, Optional
from agno.agent import Agent as AgnoAgent
from sqlalchemy.ext.asyncio import AsyncSession
from .base_team import BaseTeam

class ResearchTeam(BaseTeam):
    """
    A specialized team for comprehensive research tasks.
    
    Structure:
    - Leader: Research Coordinator (Manages the flow)
    - Member 1: Web Searcher (Uses DuckDuckGo/Google)
    - Member 2: Data Analyst (Processes findings)
    - Member 3: Writer (Summarizes results)
    """
    
    async def initialize(self, 
                         coordinator_id: str,
                         searcher_id: str, 
                         writer_id: str,
                         analyst_id: str = None) -> AgnoAgent:
        """
        Builds the research team.
        Args:
            coordinator_id: The ID of the agent acting as team leader.
            searcher_id: The ID of the web search agent.
            writer_id: The ID of the writer agent.
            analyst_id: Optional ID of the data analyst agent.
        """
        # 1. Build Members
        searcher = await self._build_member_agent(searcher_id)
        writer = await self._build_member_agent(writer_id)
        
        team_members = [searcher, writer]
        
        if analyst_id:
            analyst = await self._build_member_agent(analyst_id)
            team_members.append(analyst)
            
        self.members = team_members

        # 2. Build Coordinator (Leader)
        # We reuse the builder for the leader, but we need to inject the team members
        from app.services.eah_agent.agent.builder import AgentBuilder
        
        # We load the leader's base config
        builder = AgentBuilder(self.db, coordinator_id)
        await builder._fetch_agent_config()
        await builder._fetch_model_config()
        # Note: Tools for leader are usually just delegation tools, but we load configured ones too
        await builder._load_tools()
        
        # 3. Configure Leader Instructions for Team Management
        role_descriptions = "\n".join([f"- {m.name}: {m.description or 'No description'}" for m in team_members])
        
        team_instructions = f"""
## Team Coordination
You are the Research Coordinator. You have a team of specialized agents at your disposal:
{role_descriptions}

Your goal is to answer the user's research question comprehensively.
1. Delegate searching tasks to the Searcher.
2. If data analysis is needed, delegate to the Analyst.
3. Once information is gathered, delegate to the Writer to produce the final answer.

Do not answer from your own knowledge if the team can find better up-to-date information.
Always synthesize the final output clearly.
"""
        builder.instruction_builder.instructions += "\n" + team_instructions
        
        # 4. Construct the Leader Agent with 'team' parameter
        # In Agno, passing a list of Agents to 'team' parameter enables delegation
        from app.services.llm.factory import ModelFactory
        
        model = ModelFactory.create_model(builder.llm_model)
        final_instructions = builder.instruction_builder.build()
        
        self.team_agent = AgnoAgent(
            name=builder.agent_model.name,
            model=model,
            team=team_members, # <--- This enables Team Mode
            instructions=final_instructions,
            tools=builder.tools,
            # show_tool_calls=True,
            markdown=True,
            debug_mode=True
        )
        
        return self.team_agent
