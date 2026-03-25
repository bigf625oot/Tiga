import logging
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_model import LLMModel
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.services.eah_agent.core.executors.base_executor import BaseExecutor
from app.services.eah_agent.core.components.default_memory_manager import DefaultMemoryManager
from app.services.eah_agent.core.components.default_state_manager import DefaultStateManager
from app.services.eah_agent.core.components.default_plan_validator import DefaultPlanValidator
from app.services.eah_agent.core.components.default_experience_store import DefaultExperienceStore
from app.services.eah_agent.core.components.default_tool_registry import DefaultToolRegistry

# Engines
from app.services.eah_agent.core.engines.planning_engine import PlanningEngine
from app.services.eah_agent.core.engines.execution_engine import ExecutionEngine
from app.services.eah_agent.core.engines.evaluation_engine import EvaluationEngine
from app.services.eah_agent.core.engines.reflection_engine import ReflectionEngine

from app.services.eah_agent.document.file_orchestrator import FileOrchestrator
from app.core.i18n import _

logger = logging.getLogger("eah.executors.single")

class SingleExecutor(BaseExecutor):
    """
    单体闭环执行器 (Single Executor)
    原 plan_handler.py 的升级版。
    整合了 Planning -> Execution -> Evaluation -> Reflection 完整生命周期。
    """
    
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
            # 1. 准备上下文和文件
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
                
            # 更新状态为 planning
            if self.state_manager:
                await self.state_manager.update_status(session_id, "planning")

            # 2. 规划阶段 (Planning)
            yield {"type": "status", "content": _("Generating execution plan...")}
            
            planning_engine = PlanningEngine(db=db, llm_model=self.llm_model)
            plan_manifest = await planning_engine.generate_plan(
                session_id=session_id,
                user_goal=input_text,
                context=file_context
            )
            
            # 使用 PlanValidator 校验计划
            if self.plan_validator:
                plan_dict = {"tasks": [t.dict() for t in plan_manifest.tasks]}
                is_valid, error_msg = await self.plan_validator.validate(plan_dict, {})
                if not is_valid:
                    raise ValueError(f"Plan validation failed: {error_msg}")
            
            # 通知前端计划生成完毕
            yield {
                "type": "plan", 
                "content": json.dumps({"reasoning": plan_manifest.reasoning, "tasks": [t.dict() for t in plan_manifest.tasks]})
            }

            # 更新状态为 executing
            if self.state_manager:
                await self.state_manager.update_status(session_id, "executing")

            # 3. 执行与评估阶段 (Execution & Evaluation)
            execution_engine = ExecutionEngine(db=db, tool_registry=self.tool_registry, llm_model=self.llm_model)
            evaluation_engine = EvaluationEngine(db=db, llm_model=self.llm_model)
            
            execution_logs = []
            all_success = True
            
            # 简单顺序执行（实际可根据 DAG 进行并发控制）
            for task in plan_manifest.tasks:
                yield {"type": "status", "content": _(f"Executing task: {task.title}")}
                
                task_output = ""
                async for event in execution_engine.execute_task(task, history_msgs):
                    yield event
                    if event.get("type") == "content" and isinstance(event.get("content"), str):
                        task_output += event.get("content")
                        
                execution_logs.append(f"Task: {task.title}\nOutput: {task_output}")
                
                # 评估当前任务
                eval_result = await evaluation_engine.evaluate_result(
                    task_goal=task.description,
                    execution_result=task_output,
                    criteria=task.expected_output
                )
                
                if not eval_result.get("passed"):
                    yield {"type": "error", "content": f"Task '{task.title}' failed validation: {eval_result.get('feedback')}"}
                    all_success = False
                    break # 或者触发重试机制
            
            # 4. 反思阶段 (Reflection)
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
            yield {"type": "error", "content": _("Execution engine encountered a critical failure: ") + str(e)}

    async def _prepare_history(self, session_id: str, current_query: str = "") -> List[Dict]:
        """通过 MemoryManager 加载并压缩历史消息"""
        if self.memory_manager:
            return await self.memory_manager.get_compressed_context(session_id, current_query)
        return []
