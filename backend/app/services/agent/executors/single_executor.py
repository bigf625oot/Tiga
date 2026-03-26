# -*- coding: utf-8 -*-
import logging
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_model import LLMModel
from app.services.agent.schemas.intent import IntentResult
from app.services.agent.executors.base.base_executor import BaseExecutor
from app.services.agent.components.memory_manager import DefaultMemoryManager
from app.services.agent.components.state_manager import DefaultStateManager
from app.services.agent.components.plan_validator import DefaultPlanValidator
from app.services.agent.components.experience_store import DefaultExperienceStore
from app.services.agent.components.tool_registry import DefaultToolRegistry

# Engines
from app.services.agent.engines.planning_engine import PlanningEngine
from app.services.agent.engines.execution_engine import ExecutionEngine
from app.services.agent.engines.evaluation_engine import EvaluationEngine
from app.services.agent.engines.reflection_engine import ReflectionEngine

from app.services.agent.document.file_orchestrator import FileOrchestrator
from app.core.i18n import _

logger = logging.getLogger("eah.executors.single")

class SingleExecutor(BaseExecutor):
    """
    [State Machine] 全生命周期执行器 (Plan -> Execute -> Evaluate -> Reflect)
    Trade-offs: 采用单体大循环与有限重试策略(Harness)。牺牲执行速度，换取高容错与多步任务的闭环能力。
    """
    
    MAX_RETRIES = 3
    
    def __init__(
        self,
        llm_model: Optional[LLMModel] = None,
        memory_manager: Optional[DefaultMemoryManager] = None,
        state_manager: Optional[DefaultStateManager] = None,
        plan_validator: Optional[DefaultPlanValidator] = None,
        experience_store: Optional[DefaultExperienceStore] = None,
        tool_registry: Optional[DefaultToolRegistry] = None,
    ):
        super().__init__(
            llm_model=llm_model,
            memory_manager=memory_manager,
            state_manager=state_manager,
            plan_validator=plan_validator,
            experience_store=experience_store,
            tool_registry=tool_registry
        )

    async def execute(
        self,
        input_text: str,
        intent: IntentResult,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        db: AsyncSession = kwargs.get("db")
        session_id: str = kwargs.get("session_id")
        files: List[Any] = kwargs.get("files", [])
        
        yield {"type": "status", "content": _("Orchestrating autonomous planning environment...")}

        try:
            # 1. [Context Topology] 并发加载上下文拓扑
            setup_tasks = [
                asyncio.create_task(FileOrchestrator.process_batch(files, session_id)),
                asyncio.create_task(self._prepare_history(session_id, current_query=input_text))
            ]
            results = await asyncio.gather(*setup_tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    raise res

            file_results, history_msgs = results
            
            file_context = file_results.get("context", "") if file_results else ""
            if file_context:
                yield {"type": "status", "content": _("Contextualized with {} files.").format(len(files))}
                
            # [State Sync] 状态流转: planning
            if self.state_manager:
                await self.state_manager.update_status(session_id, "planning")

            # 2. [Planning Phase] 动态任务拆解
            yield {"type": "status", "content": _("Generating execution plan...")}
            
            planning_engine = PlanningEngine(db=db, llm_model=self.llm_model)
            plan_manifest = await planning_engine.generate_plan(
                session_id=session_id,
                user_goal=input_text,
                context=file_context
            )
            
            # [Validation] 强制计划确定性校验，阻断不合规规划
            if self.plan_validator:
                plan_dict = {"tasks": [t.dict() for t in plan_manifest.tasks]}
                is_valid, error_msg = await self.plan_validator.validate(plan_dict, {})
                if not is_valid:
                    raise ValueError(f"Plan validation failed: {error_msg}")
            
            # 閫氱煡鍓嶇璁″垝鐢熸垚瀹屾瘯
            yield {
                "type": "plan", 
                "content": json.dumps({"reasoning": plan_manifest.reasoning, "tasks": [t.dict() for t in plan_manifest.tasks]})
            }

            # [State Sync] 状态流转: executing
            if self.state_manager:
                await self.state_manager.update_status(session_id, "executing")

            # 3. [Execution & Evaluation Phase] 采用有限状态机管理重试机制
            execution_engine = ExecutionEngine(db=db, tool_registry=self.tool_registry, llm_model=self.llm_model)
            evaluation_engine = EvaluationEngine(db=db, llm_model=self.llm_model)
            
            execution_logs = []
            all_success = True
            
            # [Harness Loop] 带有自我修正的执行循环
            for task in plan_manifest.tasks:
                yield {"type": "status", "content": _(f"Executing task: {task.title}")}
                yield {"type": "execute_start", "content": task.description}
                
                succeeded = False
                for attempt in range(self.MAX_RETRIES):
                    if attempt > 0:
                        yield {"type": "status", "content": _(f"Retrying task: {task.title} (Attempt {attempt+1}/{self.MAX_RETRIES})")}
                        
                    task_output = ""
                    async for event in execution_engine.execute_task(task, history_msgs):
                        # [Stream Adapter] 过滤内部状态，防止前端渲染抖动
                        yield event
                        event_dict = event.to_dict() if hasattr(event, "to_dict") else event
                        if isinstance(event_dict, dict) and event_dict.get("type") == "content" and isinstance(event_dict.get("content"), str):
                            task_output += event_dict.get("content")
                            
                    # [Evaluation] 结果断言
                    eval_result = await evaluation_engine.evaluate_result(
                        task_goal=task.description,
                        execution_result=task_output,
                        criteria=task.expected_output
                    )
                    
                    if eval_result.get("passed"):
                        execution_logs.append(f"Task: {task.title}\nOutput: {task_output}")
                        yield {"type": "subtask_done", "content": task_output}
                        succeeded = True
                        break
                    
                    # [Reflection Loop] 未通过则触发动态修正提示注入
                    if attempt < self.MAX_RETRIES - 1:
                        yield {"type": "status", "content": _("Task failed evaluation, reflecting...")}
                        hint = await evaluation_engine.reflect(
                            task_goal=task.description,
                            execution_result=task_output,
                            feedback=eval_result.get("feedback", "")
                        )
                        yield {"type": "reflect", "content": hint}
                        # 注入反思提示供下一次执行修正上下文
                        task.reflection = hint
                    else:
                        yield {"type": "subtask_failed", "content": eval_result.get("feedback", "Max retries reached")}
                        execution_logs.append(f"Task: {task.title} (FAILED)\nOutput: {task_output}")
                
                if not succeeded:
                    yield {"type": "error", "content": f"Task '{task.title}' failed after {self.MAX_RETRIES} attempts."}
                    all_success = False
                    break
            
            # 4. [Reflection Phase] 经验沉淀与全局反思
            if self.state_manager:
                await self.state_manager.update_status(session_id, "reflecting")
                
            if self.experience_store:
                yield {"type": "status", "content": _("Reflecting on execution...")}
                reflection_engine = ReflectionEngine(db=db, experience_store=self.experience_store, llm_model=self.llm_model)
                summary = await reflection_engine.reflect_and_store(
                    session_id=session_id,
                    task_desc=input_text,
                    execution_log="\n\n".join(execution_logs),
                    is_success=all_success
                )
                if summary:
                    yield {"type": "content", "content": f"\n\n**Reflection**: {summary}"}
            
            if self.state_manager:
                await self.state_manager.update_status(session_id, "completed" if all_success else "failed")

        except Exception as e:
            logger.error(f"SingleExecutor failed: {e}", exc_info=True)
            yield self._yield_error(_("Execution engine encountered a critical failure"), e)

