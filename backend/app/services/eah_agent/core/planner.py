import logging
from typing import Dict, Any, Optional
from agno.agent import Agent as AgnoAgent
from app.models.agent_plan import AgentPlan, AgentTask
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class PlannerAgent:
    def __init__(self, agent_manager, db: AsyncSession, model_id: str = "gpt-4-turbo"):
        self.agent_manager = agent_manager
        self.db = db
        self.model_id = model_id
        self._agent = None

    async def initialize(self):
        """
        Initialize the underlying Agno Agent with a planning-specific prompt.
        In a real scenario, this might load a specific 'Planner' agent config from DB.
        For now, we create a default one.
        """
        # TODO: Load from DB or use a default configuration
        # We need a model that is good at reasoning and JSON output.
        pass

    async def create_plan(self, session_id: str, user_goal: str) -> str:
        """
        Analyzes the user goal and creates a structured plan (AgentPlan) with multiple tasks (AgentTask).
        Returns the plan_id.
        """
        logger.info(f"Creating plan for session {session_id} with goal: {user_goal}")
        
        # 1. Create the Plan record
        plan = AgentPlan(session_id=session_id, user_goal=user_goal, status="planning")
        self.db.add(plan)
        await self.db.flush() # Get ID
        
        # 2. Invoke LLM to decompose the goal
        # For Phase 1, we will implement a simple mock or direct LLM call here
        # to demonstrate the flow. In future, use self._agent.run()
        
        # Mock logic for demonstration:
        # If goal contains "code" or "python", create a coding task.
        # If goal contains "search", create a search task.
        
        tasks = []
        sequence = 1
        
        # Simple heuristic for Phase 1
        if "search" in user_goal.lower():
            tasks.append(AgentTask(
                plan_id=plan.id,
                sequence=sequence,
                name="Research",
                description=f"Search for information about: {user_goal}",
                assigned_agent_role="researcher", # We will map this to an actual agent ID later
                status="pending"
            ))
            sequence += 1
            
        if "code" in user_goal.lower() or "calculate" in user_goal.lower() or "plot" in user_goal.lower():
             tasks.append(AgentTask(
                plan_id=plan.id,
                sequence=sequence,
                name="Coding",
                description=f"Write and execute code to solve: {user_goal}",
                assigned_agent_role="coder",
                status="pending"
            ))
             sequence += 1
             
        # If no specific keywords, just one generic task
        if not tasks:
             tasks.append(AgentTask(
                plan_id=plan.id,
                sequence=sequence,
                name="General Task",
                description=user_goal,
                assigned_agent_role="general",
                status="pending"
            ))
            
        self.db.add_all(tasks)
        plan.status = "running" # Auto-start for now
        await self.db.commit()
        
        return plan.id
