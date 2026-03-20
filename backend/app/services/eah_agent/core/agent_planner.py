import logging
import asyncio
import networkx as nx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from agno.agent import Agent
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent_plan import AgentPlan, AgentTask
from app.services.llm.resolver import resolve_chat_llm_model
from app.services.llm.factory import ModelFactory
from app.core.config import settings

logger = logging.getLogger("eah.core.planner")

# --- 1. 领域模型定义 (Domain Schemas) ---

class TaskDefinition(BaseModel):
    """原子任务的结构化定义"""
    task_id: str = Field(..., description="唯一任务标识，如 'fetch_data'")
    title: str = Field(..., max_length=100)
    description: str = Field(..., description="详尽的执行步骤描述")
    dependencies: List[str] = Field(default_factory=list, description="依赖的任务 task_id 列表")
    executor_role: str = Field(..., description="执行角色，如 'sql_expert', 'web_searcher'")
    expected_output: str = Field(..., description="任务成功的衡量标准")

class PlanManifest(BaseModel):
    """LLM 生成的规划清单"""
    reasoning: str = Field(..., description="思维链分析：为什么要这样拆分任务？")
    tasks: List[TaskDefinition] = Field(..., min_items=1)

    @validator("tasks")
    def validate_logic_graph(cls, tasks):
        """核心业务校验：确保任务流是一个有向无环图 (DAG)"""
        dg = nx.DiGraph()
        task_ids = {t.task_id for t in tasks}
        
        for t in tasks:
            dg.add_node(t.task_id)
            for dep in t.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"任务 '{t.task_id}' 依赖了一个不存在的任务: '{dep}'")
                dg.add_edge(dep, t.task_id)

        if not nx.is_directed_acyclic_graph(dg):
            cycle = nx.find_cycle(dg)
            raise ValueError(f"检测到逻辑死循环，请重新规划: {cycle}")
        return tasks

# --- 2. 规划引擎实现 (The Planner Engine) ---

class PlannerAgent:
    """
    P10 级规划引擎：集成结构化输出、逻辑闭环校验与原子持久化。
    """
    def __init__(self, db: AsyncSession, model_id: Optional[str] = None):
        self.db = db
        self.model_id = model_id or "gpt-4-turbo"
        self._agent: Optional[Agent] = None
        self._init_lock = asyncio.Lock()

    async def _ensure_agent(self) -> Agent:
        """双重检查锁定模式，确保 Agent 单例安全加载"""
        if self._agent:
            return self._agent
            
        async with self._init_lock:
            if not self._agent:
                # 1. 解析模型记录
                llm_model = await resolve_chat_llm_model(self.db, model_id=self.model_id)
                model_instance = ModelFactory.create_model(llm_model)

                # 2. 装配规划者实例
                self._agent = Agent(
                    name="Lead-Architect-Planner",
                    model=model_instance,
                    # 关键优化：强制 Pydantic 响应模型，Agno 会自动重试直到通过 Schema 校验
                    response_model=PlanManifest,
                    instructions=[
                        "你是一位资深系统架构师，负责将复杂的业务目标拆解为可执行的任务流。",
                        "每个任务必须是原子性的，且有明确的 'expected_output'。",
                        "你必须明确任务间的依赖关系，严禁产生循环依赖。",
                        "在 'reasoning' 中解释你的规划策略。"
                    ],
                    max_retries=3,  # 如果校验失败（如 DAG 环），自动要求 LLM 修正
                    markdown=False,
                )
        return self._agent

    async def create_plan(self, session_id: str, user_goal: str, **ctx) -> str:
        """
        核心业务流：需求分析 -> 神经规划 -> 逻辑验证 -> 原子落库。
        """
        logger.info(f"Initiating planning for session: {session_id}")
        
        agent = await self._ensure_agent()
        
        # 1. 运行规划任务
        prompt = f"Goal: {user_goal}\nContextual Info: {ctx.get('extra_info', 'N/A')}"
        response = await agent.arun(prompt)
        
        # 此时 manifest 已经是经过 Pydantic 和自定义 validate_logic_graph 验证过的对象
        manifest: PlanManifest = response.content
        
        # 2. 原子化持久化 (Transactional Persistence)
        try:
            # 使用 SAVEPOINT 确保子事务一致性
            async with self.db.begin_nested():
                plan_id = await self._persist_plan(session_id, user_goal, manifest)
                await self.db.commit()
                return plan_id
        except Exception as e:
            logger.critical(f"Critical persistence failure for session {session_id}: {e}")
            await self.db.rollback()
            raise

    async def _persist_plan(self, session_id: str, user_goal: str, manifest: PlanManifest) -> str:
        """数据映射层：将 Manifest 转换为数据库实体"""
        # 创建主计划
        plan = AgentPlan(
            session_id=session_id,
            user_goal=user_goal,
            reasoning=manifest.reasoning,
            status="prepared"
        )
        self.db.add(plan)
        await self.db.flush() # 获取自增 ID

        # 批量创建任务
        task_entities = []
        for i, t_def in enumerate(manifest.tasks):
            task_entities.append(AgentTask(
                plan_id=plan.id,
                sequence=i + 1,
                logic_id=t_def.task_id, # 业务层逻辑标识
                name=t_def.title,
                description=t_def.description,
                dependencies=t_def.dependencies, # 存储逻辑依赖关系 JSON
                assigned_agent_role=t_def.executor_role,
                status="pending"
            ))
        
        self.db.add_all(task_entities)
        return str(plan.id)