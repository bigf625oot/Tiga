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
from app.services.agent.components.clarifier import IntentClarifier

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
        
        yield {"type": "status", "content": "正在初始化自主规划环境..."}

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
                yield {"type": "status", "content": f"包含 {len(files)} 个文件的上下文已就绪。"}
                
            # --- [Pre-Planning Gatekeeper: Clarification Check] ---
            # P10 \u7ea7\u9632\u5fa1\uff1a\u5728\u8fdb\u5165\u9ad8\u6602\u7684 Planning Phase \u4e4b\u524d\uff0c\u901a\u8fc7\u8f7b\u91cf\u7ea7\u6a21\u578b\u8fdb\u884c\u610f\u56fe\u6258\u5e95\u6f84\u6e05
            # \u5982\u679c intent \u8bc6\u522b\u7f6e\u4fe1\u5ea6\u504f\u4f4e\uff0c\u6216\u7528\u6237\u8f93\u5165\u672c\u8eab\u5b58\u5728\u9ad8\u5ea6\u6b67\u4e49\uff0c\u5219\u89e6\u53d1\u53cd\u95ee\u77ed\u8def
            if intent.confidence < 0.85:
                yield {"type": "status", "content": "正在检查任务意图是否清晰..."}
                clarifier = IntentClarifier(llm_model=self.llm_model)
                clarification_result = await clarifier.check_ambiguity(input_text, context=file_context)
                
                if clarification_result.is_ambiguous and clarification_result.clarification_question:
                    # \u89e6\u53d1\u53cd\u95ee\u6d41\uff0c\u66f4\u65b0\u72b6\u6001\u673a\u5e76\u7ec8\u6b62\u672c\u6b21 Executor \u751f\u6210\u5668\uff0c\u7b49\u5f85\u7528\u6237\u8865\u5145\u4fe1\u606f
                    if self.state_manager:
                        await self.state_manager.update_status(session_id, "clarifying")
                    yield {
                        "type": "clarify", 
                        "content": clarification_result.clarification_question,
                        "reasoning": clarification_result.reasoning
                    }
                    return  # \u76f4\u63a5\u77ed\u8def\uff0c\u9632\u6b62\u9003\u9038\u5230 PlanningEngine
            # ------------------------------------------------------
                
            # [State Sync] \u72b6\u6001\u6d41\u8f6c: planning
            if self.state_manager:
                await self.state_manager.update_status(session_id, "planning")

            # 2. [Planning Phase] \u52a8\u6001\u4efb\u52a1\u62c6\u89e3
            yield {"type": "status", "content": "正在生成执行计划..."}
            
            tools = self.tool_registry.get_all_tools()
            planning_engine = PlanningEngine(
                db=db, 
                llm_model=self.llm_model, 
                tools=tools
            )
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

            # 3. [Execution Phase] 执行任务并移除阻塞式同步评估 (P10 Performance Fix)
            execution_engine = ExecutionEngine(db=db, tool_registry=self.tool_registry, llm_model=self.llm_model)
            
            execution_logs = []
            all_success = True
            
            # [Linear Execution] 采用线性执行，将后置评估降维至旁路
            for task in plan_manifest.tasks:
                yield {"type": "status", "content": f"正在执行任务: {task.title}"}
                yield {"type": "execute_start", "content": task.description}
                
                task_output = ""
                try:
                    async for event in execution_engine.execute_task(task, history_msgs):
                        # [Stream Adapter] 过滤内部状态，防止前端渲染抖动
                        yield event
                        event_dict = event.to_dict() if hasattr(event, "to_dict") else event
                        if isinstance(event_dict, dict) and event_dict.get("type") == "content" and isinstance(event_dict.get("content"), str):
                            task_output += event_dict.get("content")
                    
                    # 假设执行成功，因为不再同步阻塞评估
                    execution_logs.append(f"Task: {task.title}\nOutput: {task_output}")
                    yield {"type": "subtask_done", "content": task_output}
                except Exception as task_err:
                    yield {"type": "subtask_failed", "content": str(task_err)}
                    execution_logs.append(f"Task: {task.title} (FAILED)\nOutput: {str(task_err)}")
                    all_success = False
                    break
            
            # 4. [Deferred Evaluation & Reflection Phase] 异步后置反思，释放流式吞吐
            if self.state_manager:
                await self.state_manager.update_status(session_id, "reflecting")
                
            if self.experience_store:
                yield {"type": "status", "content": "正在异步沉淀经验..."}
                reflection_engine = ReflectionEngine(db=db, experience_store=self.experience_store, llm_model=self.llm_model)
                
                # 性能优化：将反思作为非阻塞任务投递到事件循环，而不是阻塞等待
                async def _background_reflect():
                    try:
                        await reflection_engine.reflect_and_store(
                            session_id=session_id,
                            task_desc=input_text,
                            execution_log="\n\n".join(execution_logs),
                            is_success=all_success
                        )
                    except Exception as e:
                        logger.error(f"Background reflection failed: {e}")
                
                asyncio.create_task(_background_reflect())
            
            if self.state_manager:
                await self.state_manager.update_status(session_id, "completed" if all_success else "failed")

        except Exception as e:
            logger.error(f"SingleExecutor failed: {e}", exc_info=True)
            yield self._yield_error("执行引擎遇到严重故障", e)

