import logging
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_model import LLMModel
from app.services.eah_agent.schemas.intent import IntentResult
from app.services.eah_agent.executors.base_executor import BaseExecutor
from app.services.eah_agent.components.memory_manager import DefaultMemoryManager
from app.services.eah_agent.components.state_manager import DefaultStateManager
from app.services.eah_agent.components.plan_validator import DefaultPlanValidator
from app.services.eah_agent.components.experience_store import DefaultExperienceStore
from app.services.eah_agent.components.tool_registry import DefaultToolRegistry

# Engines
from app.services.eah_agent.engines.planning_engine import PlanningEngine
from app.services.eah_agent.engines.execution_engine import ExecutionEngine
from app.services.eah_agent.engines.evaluation_engine import EvaluationEngine
from app.services.eah_agent.engines.reflection_engine import ReflectionEngine

from app.services.eah_agent.document.file_orchestrator import FileOrchestrator
from app.core.i18n import _

logger = logging.getLogger("eah.executors.single")

class SingleExecutor(BaseExecutor):
    """
    Single Executor (Monolithic Loop)
    An upgraded version of plan_handler.py and PlanAgent.
    Integrates the full lifecycle: Planning -> Execution -> Evaluation -> Reflection.
    Introduces Harness mode with retry mechanisms and reflection loops.
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
            # 1. 鍑嗗涓婁笅鏂囧拰鏂囦欢
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
                
            # 鏇存柊鐘舵€佷负 planning
            if self.state_manager:
                await self.state_manager.update_status(session_id, "planning")

            # 2. 瑙勫垝闃舵 (Planning)
            yield {"type": "status", "content": _("Generating execution plan...")}
            
            planning_engine = PlanningEngine(db=db, llm_model=self.llm_model)
            plan_manifest = await planning_engine.generate_plan(
                session_id=session_id,
                user_goal=input_text,
                context=file_context
            )
            
            # 浣跨敤 PlanValidator 鏍￠獙璁″垝
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

            # 鏇存柊鐘舵€佷负 executing
            if self.state_manager:
                await self.state_manager.update_status(session_id, "executing")

            # 3. 鎵ц涓庤瘎浼伴樁娈?(Execution & Evaluation)
            execution_engine = ExecutionEngine(db=db, tool_registry=self.tool_registry, llm_model=self.llm_model)
            evaluation_engine = EvaluationEngine(db=db, llm_model=self.llm_model)
            
            execution_logs = []
            all_success = True
            
            # 绠€鍗曢『搴忔墽琛岋紙甯︽湁閲嶈瘯涓庡弽鎬濇満鍒讹級
            for task in plan_manifest.tasks:
                yield {"type": "status", "content": _(f"Executing task: {task.title}")}
                yield {"type": "execute_start", "content": task.description}
                
                succeeded = False
                for attempt in range(self.MAX_RETRIES):
                    if attempt > 0:
                        yield {"type": "status", "content": _(f"Retrying task: {task.title} (Attempt {attempt+1}/{self.MAX_RETRIES})")}
                        
                    task_output = ""
                    async for event in execution_engine.execute_task(task, history_msgs):
                        # 杩囨护鎺夊唴閮ㄤ骇鐢熺殑鏅€?status 浠ュ厤鍒峰睆锛屾垨鑰呴€夋嫨閫忎紶
                        yield event
                        if event.get("type") == "content" and isinstance(event.get("content"), str):
                            task_output += event.get("content")
                            
                    # 璇勪及褰撳墠浠诲姟
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
                    
                    # 濡傛灉鏈€氳繃锛岃繘琛屽弽鎬濆苟鍑嗗涓嬩竴娆￠噸璇?
                    if attempt < self.MAX_RETRIES - 1:
                        yield {"type": "status", "content": _("Task failed evaluation, reflecting...")}
                        hint = await evaluation_engine.reflect(
                            task_goal=task.description,
                            execution_result=task_output,
                            feedback=eval_result.get("feedback", "")
                        )
                        yield {"type": "reflect", "content": hint}
                        # 娉ㄥ叆鍙嶆€濇彁绀虹粰涓嬩竴娆℃墽琛?
                        task.reflection = hint
                    else:
                        yield {"type": "subtask_failed", "content": eval_result.get("feedback", "Max retries reached")}
                        execution_logs.append(f"Task: {task.title} (FAILED)\nOutput: {task_output}")
                
                if not succeeded:
                    yield {"type": "error", "content": f"Task '{task.title}' failed after {self.MAX_RETRIES} attempts."}
                    all_success = False
                    break
            
            # 4. 鍙嶆€濋樁娈?(Reflection)
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

