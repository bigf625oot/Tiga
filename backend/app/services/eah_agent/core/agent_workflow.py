import asyncio
import json
import logging
import re
import time
import networkx as nx
from enum import Enum
from typing import AsyncGenerator, Dict, Any, Optional, List, Set, Union, Literal
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator

# 外部框架依赖
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from agno.agent import Agent as AgnoAgent

# 内部依赖 (假设路径)
from app.models.agent import Agent as AgentModel
from app.models.agent_plan import AgentPlan, AgentTask, PlanStatus, TaskStatus
from app.services.llm.factory import ModelFactory
from app.services.llm.resolver import resolve_chat_llm_model
from app.services.eah_agent.utils.agno_compat import filter_init_kwargs
from app.core.config import settings
from app.core.i18n import _

logger = logging.getLogger("agno.unified_engine")

# =================================================================
# 1. 领域模型与协议层 (Domain & Schemas)
# =================================================================

class IntentType(str, Enum):
    CHAT = "chat"
    TASK = "task"
    DATA = "data_query"
    FLOW = "workflow"

class StreamType(str, Enum):
    THINK = "think"
    CONTENT = "content"
    STATUS = "status"
    ERROR = "error"
    NODE_DONE = "node_done"

class IntentResult(BaseModel):
    intent: IntentType
    confidence: float
    reasoning: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class TaskDefinition(BaseModel):
    task_id: str
    title: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    executor_role: str = "default"
    ui_component: str = "markdown"

class PlanManifest(BaseModel):
    reasoning: str
    tasks: List[TaskDefinition]

    @validator("tasks")
    def validate_dag(cls, v):
        dg = nx.DiGraph()
        ids = {t.task_id for t in v}
        for t in v:
            dg.add_node(t.task_id)
            for dep in t.dependencies:
                if dep not in ids: raise ValueError(f"Missing dependency: {dep}")
                dg.add_edge(dep, t.task_id)
        if not nx.is_directed_acyclic_graph(dg):
            raise ValueError("Circular dependency detected in plan logic")
        return v

# =================================================================
# 2. 核心组件层 (Core Engines)
# =================================================================

class NluEngine:
    """高性能意图分析引擎"""
    _GREETINGS = {"你好", "hello", "hi", "在吗", "嗨"}

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(self, user_input: str) -> IntentResult:
        # Fast Path
        clean_text = re.sub(r'[^\w\s]', '', user_input.strip().lower())
        if not clean_text or clean_text in self._GREETINGS:
            return IntentResult(intent=IntentType.CHAT, confidence=1.0, reasoning="Fast-path match")

        # LLM Analysis
        llm_model = await resolve_chat_llm_model(self.db)
        model = ModelFactory.create_model(llm_model)
        
        agent = AgnoAgent(
            model=model,
            response_model=IntentResult,
            instructions=["Classify user intent into: chat, task, data_query, workflow."]
        )
        res = await agent.arun(user_input)
        return res.content

class AgentAssembler:
    """智能体全自动装配流水线"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def assemble(self, agent_id: str, **overrides) -> AgnoAgent:
        # 加载 DB 配置
        res = await self.db.execute(select(AgentModel).filter(AgentModel.id == agent_id))
        record = res.scalars().first()
        if not record: raise ValueError("Agent not found")

        llm_record = await resolve_chat_llm_model(self.db, record.model_id)
        model = ModelFactory.create_model(llm_record)

        # 厂商适配 (DeepSeek R1 etc.)
        if (llm_record.provider or "").lower() == "deepseek":
            if hasattr(model, "extra_body"): model.extra_body = {"thinking": {"type": "enabled"}}

        init_args = {
            "name": record.name,
            "model": model,
            "instructions": [record.system_prompt] if record.system_prompt else [],
            "markdown": True,
            "show_tool_calls": True,
            **overrides
        }
        return AgnoAgent(**filter_init_kwargs(AgnoAgent.__init__, init_args))

class WorkflowOrchestrator:
    """DAG 并行任务调度引擎"""
    def __init__(self, db: AsyncSession, assembler: AgentAssembler):
        self.db = db
        self.assembler = assembler
        self.event_queue = asyncio.Queue()

    async def execute_plan(self, plan_id: int) -> AsyncGenerator[Dict[str, Any], None]:
        stmt = select(AgentPlan).where(AgentPlan.id == plan_id).options(selectinload(AgentPlan.tasks))
        plan = (await self.db.execute(stmt)).scalars().first()
        plan.status = PlanStatus.RUNNING
        await self.db.commit()

        context = plan.context or {}
        running_nodes = set()

        while any(t.status in [TaskStatus.PENDING, TaskStatus.RUNNING] for t in plan.tasks):
            # 获取可执行节点 (依赖已满足)
            completed_ids = {t.logic_id for t in plan.tasks if t.status == TaskStatus.COMPLETED}
            runnable = [t for t in plan.tasks if t.status == TaskStatus.PENDING and set(t.dependencies or []).issubset(completed_ids)]

            for task in runnable:
                running_nodes.add(task.logic_id)
                asyncio.create_task(self._run_node(task, plan, context, running_nodes))

            if not runnable and not running_nodes: break # 死锁或完成

            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                yield event
            except asyncio.TimeoutError: continue

        plan.status = PlanStatus.COMPLETED
        await self.db.commit()

    async def _run_node(self, task, plan, context, running_set):
        task.status = TaskStatus.RUNNING
        await self.db.commit()
        
        try:
            agent = await self.assembler.assemble(agent_id=plan.agent_id or "default")
            full_output = ""
            async for chunk in agent.astream(task.description):
                content = chunk.get("content", "")
                full_output += content
                if content: await self.event_queue.put({"type": "content", "node": task.logic_id, "content": content})
            
            task.status = TaskStatus.COMPLETED
            task.result = full_output
            context[task.logic_id] = {"output": full_output}
            await self.event_queue.put({"type": "node_done", "node": task.logic_id, "content": full_output})
        except Exception as e:
            task.status = TaskStatus.FAILED
            await self.event_queue.put({"type": "error", "content": str(e)})
        finally:
            running_set.remove(task.logic_id)
            await self.db.commit()

# =================================================================
# 3. 业务处理器层 (Handlers)
# =================================================================

class BaseHandler:
    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        if False: yield

class PlanHandler(BaseHandler):
    """复杂任务规划处理器"""
    async def process(self, input_text, intent, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        db = kwargs.get("db")
        assembler = AgentAssembler(db)
        
        yield {"type": "status", "content": "Architecting plan..."}
        planner = await assembler.assemble(agent_id=kwargs.get("agent_id"), response_model=PlanManifest)
        
        res = await planner.arun(input_text)
        manifest: PlanManifest = res.content
        
        # 持久化 Plan
        plan = AgentPlan(session_id=kwargs.get("session_id"), user_goal=input_text, reasoning=manifest.reasoning)
        db.add(plan)
        await db.flush()
        
        for i, t in enumerate(manifest.tasks):
            db.add(AgentTask(plan_id=plan.id, logic_id=t.task_id, name=t.title, description=t.description, dependencies=t.dependencies, sequence=i))
        await db.commit()

        # 启动工作流引擎
        engine = WorkflowOrchestrator(db, assembler)
        async for event in engine.execute_plan(plan.id):
            yield event

# =================================================================
# 4. 统一控制平面 (The Unified Control Plane)
# =================================================================

class AgnoControlPlane:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.nlu = NluEngine(db)
        self.handlers = {
            IntentType.TASK: PlanHandler(),
            IntentType.CHAT: BaseHandler() # 简易处理器
        }

    async def execute(self, user_input: str, agent_id: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        # 1. 并行预处理
        nlu_task = asyncio.create_task(self.nlu.analyze(user_input))
        
        yield {"type": "status", "content": "Analyzing intent..."}
        intent_res = await nlu_task
        
        # 2. 路由分发
        handler = self.handlers.get(intent_res.intent, self.handlers[IntentType.CHAT])
        
        # 3. 流式执行
        async for event in handler.process(
            input_text=user_input,
            intent=intent_res,
            db=self.db,
            agent_id=agent_id,
            session_id=session_id
        ):
            yield event


class AgentWorkflowEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_workflow(
        self,
        session_id: str,
        user_goal: str,
        agent_instance: Any = None,
        media_objects: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        images = []
        if media_objects:
            for m in media_objects:
                path = getattr(m, "filepath", None)
                if path:
                    images.append(str(path))

        workflow = UnifiedAgentWorkflow(session_id=session_id, db=self.db, user_goal=user_goal, images=images)
        async for event in workflow.run_stream():
            yield event

# =================================================================
# 5. 使用示例 (API Entrypoint)
# =================================================================
# @router.post("/chat")
# async def chat(user_input: str, agent_id: str, session_id: str, db: AsyncSession = Depends(get_db)):
#     cp = AgnoControlPlane(db)
#     return StreamingResponse(cp.execute(user_input, agent_id, session_id))
