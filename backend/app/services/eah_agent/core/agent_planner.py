import logging
import asyncio
import hashlib
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
        self.model_id = model_id
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
                    instructions=[
                        "你是一位资深系统架构师，负责将复杂的业务目标拆解为可执行的任务流。",
                        "每个任务必须是原子性的，且有明确的 'expected_output'。",
                        "你必须明确任务间的依赖关系，严禁产生循环依赖。",
                        "仅输出一个 JSON 对象，不要解释，不要 Markdown，不要代码块。",
                        "JSON 顶层必须包含 keys: steps, estimated_reasoning。",
                        "steps 是数组；每个元素必须包含: id(int), task(str), tool_name(str), dependencies(int[])。",
                        "id 从 1 开始递增；dependencies 只能引用已出现的更小 id。",
                        "estimated_reasoning 用于解释规划策略。"
                    ],
                    retries=3,  # 在新版 agno 中 max_retries 可能变为了 retries
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
        prompt = f"""
        User Goal: {user_goal}
        Contextual Info: {ctx.get('extra_info', 'N/A')}
        
        Please ensure that the 'task' description and 'estimated_reasoning' are in the same language as the User Goal.
        """
        
        from app.services.eah_agent.core.schema import PlanValidationError, TaskPlan, parse_task_plan

        agent.response_model = TaskPlan

        response = await agent.arun(prompt)
        raw_plan = response.content if hasattr(response, "content") else response
        try:
            raw_text = raw_plan if isinstance(raw_plan, str) else str(raw_plan)
            try:
                plan = parse_task_plan(raw_plan)
            except PlanValidationError:
                repair_src = raw_text
                if len(repair_src) > 6000:
                    repair_src = repair_src[:6000]

                repair_prompt = (
                    "把下面内容转换为严格 JSON，对齐如下 schema：\n"
                    '{"steps":[{"id":1,"task":"...","tool_name":"...","dependencies":[0]}],"estimated_reasoning":"..."}\n'
                    "要求：\n"
                    "1) 只输出 JSON 对象；不要 Markdown；不要代码块；不要额外文字。\n"
                    "2) steps[].id 从 1 开始递增；dependencies 只能引用更小 id。\n"
                    "3) tool_name 必须是字符串。\n"
                    "内容如下：\n"
                    f"{repair_src}"
                )
                repair_resp = await agent.arun(repair_prompt)
                repair_raw = repair_resp.content if hasattr(repair_resp, "content") else repair_resp
                plan = parse_task_plan(repair_raw)

            manifest = PlanManifest(
                reasoning=plan.estimated_reasoning,
                tasks=[
                    TaskDefinition(
                        task_id=str(step.id),
                        title=step.task,
                        description=step.task,
                        dependencies=[str(d) for d in step.dependencies],
                        executor_role=step.tool_name,
                        expected_output="Execute successfully",
                    )
                    for step in plan.steps
                ],
            )
        except Exception as e:
            raw_text = raw_plan if isinstance(raw_plan, str) else str(raw_plan)
            sha = hashlib.sha256(raw_text.encode("utf-8", errors="ignore")).hexdigest()[:12]
            logger.error(f"Plan validation failed: {e} (raw_type={type(raw_plan)}, len={len(raw_text)}, sha={sha})")
            logger.error(f"Raw plan output: {raw_text[:2000]}")
            raise PlanValidationError(f"Invalid plan format returned by LLM: {e}")
        
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
        from app.models.agent_plan import PlanStatus
        
        # 创建主计划
        plan = AgentPlan(
            session_id=session_id,
            user_goal=user_goal,
            # reasoning=manifest.reasoning,  # AgentPlan doesn't have a reasoning column
            status=PlanStatus.PLANNING
        )
        self.db.add(plan)
        await self.db.flush() # 获取自增 ID

        # 批量创建任务
        task_entities = []
        for i, t_def in enumerate(manifest.tasks):
            task_entities.append(AgentTask(
                plan_id=plan.id,
                sequence=i + 1,
                # logic_id=t_def.task_id, # AgentTask doesn't have logic_id
                name=t_def.title,
                description=t_def.description,
                dependencies=t_def.dependencies, # 存储逻辑依赖关系 JSON
                assigned_agent_role=t_def.executor_role,
                status="pending"
            ))
        
        self.db.add_all(task_entities)
        return str(plan.id)
