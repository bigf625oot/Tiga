import logging
import re
from enum import Enum
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.llm_model import LLMModel
from app.services.agent.schemas.intent import IntentResult
from app.services.agent.orchestration.nlu import NluService

logger = logging.getLogger("eah.core.router")

# ---------------------------------------------------------------------------
# 启发式正则拦截规则 (从 classifier 迁移，实现零延迟降维打击)
# ---------------------------------------------------------------------------
_TASK_PATTERNS = [
    # 任务型动词
    r"帮我(完成|实现|开发|制作|搭建|构建|创建|写一个|生成)",
    r"(制定|规划|设计|制作)(一?个?)(方案|计划|流程|步骤|大纲|报告)",
    r"(分步|逐步|一步一步|step.?by.?step)",
    r"(完整的|系统的|全面的).{0,10}(分析|报告|方案|计划)",
    r"(先.{1,10}然后.{1,10}最后|首先.{1,10}接着.{1,10}最终)",
    # 英文
    r"\b(create|build|implement|develop|design|generate)\b.{0,20}\b(plan|step|workflow)\b",
    r"\bstep[- ]by[- ]step\b",
    r"\b(multi[- ]?step|multi[- ]?stage)\b",
]

_CHAT_PATTERNS = [
    # 查询型
    r"^(什么是|who is|what is|how does|为什么|怎么|如何|解释|介绍).{0,50}[？?]?$",
    r"(翻译|总结|摘要|概括).{0,20}(这段|以下|下面|上面)",
    r"(现在|今天|当前|最新|最近).{0,10}(天气|新闻|股价|汇率|价格)",
    # 英文
    r"^(what|who|when|where|why|how)\b.{0,60}[?]?$",
    r"\b(summarize|translate)\b",
]

_TASK_RE = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _TASK_PATTERNS]
_CHAT_RE = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _CHAT_PATTERNS]

def _heuristic_classify(message: str) -> Optional[IntentResult]:
    """零延迟启发式意图拦截"""
    for pat in _TASK_RE:
        if pat.search(message):
            return IntentResult(
                intent="task",
                confidence=0.85,
                reasoning=f"Heuristic matched task pattern: {pat.pattern[:40]}",
                parameters={},
            )
    for pat in _CHAT_RE:
        if pat.search(message):
            return IntentResult(
                intent="chat",
                confidence=0.85,
                reasoning=f"Heuristic matched chat pattern: {pat.pattern[:40]}",
                parameters={},
            )

    # 消息很短（< 4 字）且不包含明显任务指令，通常是简单问答 (如 "你好", "在吗")
    if len(message.strip()) < 4:
        return IntentResult(
            intent="chat",
            confidence=0.7,
            reasoning="Short message heuristic (<4 chars)",
            parameters={},
        )
    return None

class ModeRouter:
    """
    负责接收请求、执行 NLU 意图分析，并将任务分发给相应的 Executor。
    目前已完成向 Executor 架构的迁移，旧的 Handler 逻辑已被移除。
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model
        
    async def route_request(self, user_input: str, db: AsyncSession, kwargs: Dict[str, Any], resolved_intent: Optional[IntentResult] = None) -> tuple[Any, IntentResult]:
        """
        进行意图分析并返回目标执行器 (Executor) 以及意图结果。
        若调用方已解析意图（如 AgnoControlPlane），直接传入 resolved_intent 跳过重复 NLU 调用。
        """
        intent = resolved_intent if resolved_intent is not None else await self._resolve_intent(user_input, kwargs)
        intent_key = intent.intent.value if isinstance(intent.intent, Enum) else str(intent.intent)
        logger.info(f"Routing request based on intent: {intent_key}")

        # 初始化共享组件
        from app.services.agent.components import (
            DefaultMemoryManager,
            DefaultStateManager,
            DefaultPlanValidator,
            DefaultExperienceStore,
            DefaultToolRegistry
        )
        from app.services.agent.orchestration.builder import AgentAssembler

        memory_manager = DefaultMemoryManager(db=db, llm_model=self.llm_model)
        state_manager = DefaultStateManager(db=db)
        plan_validator = DefaultPlanValidator()
        experience_store = DefaultExperienceStore(db=db)
        tool_registry = DefaultToolRegistry(db=db)
        
        # 将 Assembler 中装配出的工具注册到 registry
        agent_id = kwargs.get("agent_id")
        session_id = kwargs.get("session_id")
        enable_search = kwargs.get("enable_search", True)
        
        try:
            assembler = AgentAssembler(db, agent_id)
            await assembler._load_essential_data()
            await assembler._assemble_toolset(session_id=session_id, enable_search=enable_search)
            
            for tool in assembler.ctx.tools:
                if callable(tool):
                    tool_registry.register_tool(
                        name=getattr(tool, "__name__", str(tool)),
                        func=tool,
                        description=getattr(tool, "__doc__", "") or f"Tool {tool}",
                    )
                else:
                    # Toolkit instance
                    name = getattr(tool, "name", getattr(tool, "_name", str(tool)))
                    desc = getattr(tool, "description", getattr(tool, "_description", f"Toolkit {name}"))
                    tool_registry.register_tool(
                        name=name,
                        func=tool,
                        description=desc,
                    )
        except Exception as e:
            logger.warning(f"Failed to pre-assemble tools for registry: {e}")

        # 根据意图进行分发
        if intent_key in ("chat", "quick", "data_query", "kg_qa"):
            from app.services.agent.executors.fast_executor import FastExecutor
            executor = FastExecutor(llm_model=self.llm_model, memory_manager=memory_manager)

        elif intent_key == "task":
            from app.services.agent.executors.single_executor import SingleExecutor
            executor = SingleExecutor(
                llm_model=self.llm_model,
                memory_manager=memory_manager,
                state_manager=state_manager,
                plan_validator=plan_validator,
                experience_store=experience_store,
                tool_registry=tool_registry
            )

        elif intent_key == "team":
            from app.services.agent.executors.team_executor import TeamExecutor
            executor = TeamExecutor(
                llm_model=self.llm_model,
                memory_manager=memory_manager,
                state_manager=state_manager,
                plan_validator=plan_validator,
                experience_store=experience_store,
                tool_registry=tool_registry
            )

        elif intent_key == "workflow":
            from app.services.agent.executors.workflow_executor import WorkflowExecutor
            executor = WorkflowExecutor(
                llm_model=self.llm_model,
                memory_manager=memory_manager,
                state_manager=state_manager,
                plan_validator=plan_validator,
                experience_store=experience_store,
                tool_registry=tool_registry
            )

        else:
            logger.warning(f"Unknown intent {intent_key}, falling back to FastExecutor")
            from app.services.agent.executors.fast_executor import FastExecutor
            executor = FastExecutor(llm_model=self.llm_model, memory_manager=memory_manager)

        return executor, intent

    async def _resolve_intent(self, user_input: str, kwargs: Dict[str, Any]) -> IntentResult:
        """解析用户意图"""
        import asyncio
        
        forced = self._get_forced_intent(kwargs)
        if forced:
            return IntentResult(intent=forced, confidence=1.0, reasoning="Forced intent override.", parameters={})

        # 零延迟启发式预判拦截
        heuristic_intent = _heuristic_classify(user_input)
        if heuristic_intent:
            return heuristic_intent

        try:
            nlu_service = NluService(self.llm_model)
            return await asyncio.wait_for(nlu_service.analyze(user_input), timeout=6.0)
        except Exception as e:
            logger.warning(f"NLU failed or timed out: {e}. Falling back safely based on context.")
            
            # P10 确定性修复：不硬编码 fallback 到 chat。如果当前是在明确的上下文或指令下，应保留其意图。
            # 如果请求中带有明确的 task 或 plan 相关参数，回退到 task；否则默认 chat。
            fallback_intent = "chat"
            if kwargs.get("agent_id") or "plan" in user_input.lower() or "task" in user_input.lower():
                fallback_intent = "task"
                
            return IntentResult(
                intent=fallback_intent,
                confidence=0.0,
                reasoning=f"Router fallback: {e}",
                parameters={},
            )

    def _get_forced_intent(self, kwargs: Dict) -> Optional[str]:
        mode_map = {
            "quick": "quick", "chat": "chat",
            "plan": "task", "task": "task", "solo": "task",
            "team": "team",
            "flow": "workflow", "workflow": "workflow",
            "data": "data_query", "kg": "kg_qa"
        }
        requested = kwargs.get("mode") or kwargs.get("intent_override")
        if isinstance(requested, str):
            return mode_map.get(requested.lower())
        return None
