import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent_plan import AgentPlan, AgentTask, PlanStatus, TaskStatus
from app.services.agent.manager import agent_manager

logger = logging.getLogger(__name__)

class AgentWorkflowEngine:
    """
    Orchestrates the execution of Agent Plans and Tasks.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_workflow(self, session_id: str, user_goal: str) -> str:
        """
        Starts a new workflow:
        1. Gets a Planner Agent.
        2. Creates a Plan and Tasks (persisted).
        3. Kicks off execution.
        """
        logger.info(f"Starting workflow for session {session_id}")
        
        # 1. Get Planner
        planner = await agent_manager.get_planner_agent(self.db)
        
        # 2. Create Plan (this saves to DB)
        plan_id = await planner.create_plan(session_id, user_goal)
        
        # 3. Execute
        await self.execute_plan(plan_id)
        
        return plan_id

    async def execute_plan(self, plan_id: str):
        """
        Executes tasks in a plan sequentially (for now).
        """
        logger.info(f"Executing plan {plan_id}")
        
        # Load Plan
        result = await self.db.execute(select(AgentPlan).filter(AgentPlan.id == plan_id))
        plan = result.scalars().first()
        if not plan:
            logger.error(f"Plan {plan_id} not found")
            return

        plan.status = PlanStatus.RUNNING
        await self.db.commit()

        # Get Executor
        executor = await agent_manager.get_executor_agent(self.db)

        # Loop through pending tasks
        while True:
            # Fetch next pending task ordered by sequence
            stmt = select(AgentTask).filter(
                AgentTask.plan_id == plan_id,
                AgentTask.status == TaskStatus.PENDING
            ).order_by(AgentTask.sequence.asc())
            
            res = await self.db.execute(stmt)
            task = res.scalars().first()
            
            if not task:
                logger.info("No more pending tasks.")
                break
                
            logger.info(f"Picked up task {task.name} ({task.id})")
            
            try:
                # Execute
                await executor.execute_task(task)
            except Exception as e:
                logger.error(f"Workflow stopped due to task failure: {e}")
                plan.status = PlanStatus.FAILED
                await self.db.commit()
                return

        # Check if all tasks completed
        stmt = select(AgentTask).filter(
            AgentTask.plan_id == plan_id,
            AgentTask.status != TaskStatus.COMPLETED,
            AgentTask.status != TaskStatus.SKIPPED
        )
        res = await self.db.execute(stmt)
        remaining = res.scalars().all()
        
        if not remaining:
            plan.status = PlanStatus.COMPLETED
            logger.info(f"Plan {plan_id} completed successfully.")
        else:
            logger.warning(f"Plan {plan_id} finished loop but has incomplete tasks (maybe failed?).")
            
        await self.db.commit()
