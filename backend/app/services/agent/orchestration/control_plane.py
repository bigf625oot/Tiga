import asyncio
import logging
import time
from typing import Dict, Any, Optional, AsyncGenerator, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.i18n import _
from app.models.llm_model import LLMModel
from app.services.agent.orchestration.nlu import NluService
from app.services.agent.schemas.intent import IntentResult
from app.services.agent.storage.session_history import SessionHistory
from app.services.intelligence.knowledge.rag.retrieval.engines.lightrag import lightrag_engine

logger = logging.getLogger("agno.control_plane")

@dataclass
class OrchestrationContext:
    """编排上下文：贯穿请求全生命周期的状态机"""
    user_input: str
    db: AsyncSession
    session_id: str
    kwargs: Dict[str, Any]
    start_time: float = field(default_factory=time.time)
    intent: Optional[IntentResult] = None
    knowledge_fragment: str = ""
    history_manager: Optional[SessionHistory] = None
    full_response: str = ""
    full_reasoning: str = ""
    collected_tools: List[Dict[str, Any]] = field(default_factory=list)

class StreamAggregator:
    """流式聚合器：在不阻塞流响应的情况下，实时收集数据用于最后入库"""
    def __init__(self):
        self.content = []
        self.reasoning = []
        self.tool_calls = {}
        self.stream_events = []

    def consume(self, chunk: Dict[str, Any]):
        ctype = chunk.get("type", "message")
        content = chunk.get("content")
        
        # 将内部事件类型映射为前端期望的 SSE 事件类型，并收集以供持久化
        sse_event = ctype
        if ctype == "content":
            sse_event = "text"
            
        self.stream_events.append({
            "event": sse_event,
            "content": content if content is not None else chunk,
            "raw": chunk
        })

        if ctype == "content" and isinstance(content, str):
            self.content.append(content)
        elif ctype == "think" and isinstance(content, str):
            self.reasoning.append(content)
        elif ctype == "run_output":
            # 聚合 Tool Call 详情
            data = chunk.get("data") or chunk.get("content")
            if isinstance(data, dict) and "tools" in data:
                for t in data["tools"]:
                    tid = t.get("tool_call_id") or f"unknown_{time.time()}"
                    self.tool_calls[tid] = t

    def finalize(self) -> Tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        return "".join(self.content), "".join(self.reasoning), list(self.tool_calls.values()), self.stream_events

class AgnoControlPlane:
    """
    智能体控制平面：基于协程编排的异步引擎。
    采用了策略模式处理业务逻辑，并发模型处理 I/O 密集型任务。
    """

    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model

    async def stop(self) -> None:
        return None

    async def process(
        self,
        user_input: str,
        db: AsyncSession,
        session_id: str,
        **kwargs: Any,
    ) -> str:
        """
        同步执行方法（等待完整结果返回）。
        """
        full_response = ""
        async for chunk in self.process_stream(user_input, db, session_id, **kwargs):
            if chunk.get("type") == "content":
                content = chunk.get("content")
                if isinstance(content, str):
                    full_response += content
            elif chunk.get("type") == "error":
                full_response += f"\n[Error: {chunk.get('content')}]"
        return full_response

    async def process_stream(
        self,
        user_input: str,
        db: AsyncSession,
        session_id: str,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        核心编排入口：实现极致并行的 RAG + NLU + History 加载。
        """
        ctx = OrchestrationContext(user_input=user_input, db=db, session_id=session_id, kwargs=kwargs)
        aggregator = StreamAggregator()
        persist_assistant_message = bool(ctx.kwargs.get("persist_assistant_message", True))

        try:
            # Step 1: 预热 (模型解析)
            await self._ensure_models(db)

            # Step 2: 极致并行 (NLU, RAG, History 同时启动)
            # 我们不等待所有任务完成，而是先启动，按需 await
            nlu_task = asyncio.create_task(self._resolve_intent(ctx))
            rag_task = asyncio.create_task(self._fetch_knowledge(ctx))
            history_init_task = asyncio.create_task(self._init_history(ctx))

            yield {"type": "status", "content": _("Orchestrating context...")}

            # Step 3: 等待核心决策数据 (NLU)
            ctx.intent = await nlu_task
            await history_init_task # 确保用户消息已落库
            
            # Step 4: 等待知识增强 (RAG)
            ctx.knowledge_fragment = await rag_task
            
            # Step 5: 构造增强输入
            augmented_input = self._build_prompt(ctx)

            # Step 6: 路由分发与流式输出 — 将已解析的 intent 直接注入 router，消除第二次 NLU 调用
            from app.services.agent.orchestration.router import ModeRouter
            router = ModeRouter(self.llm_model)
            executor, intent = await router.route_request(ctx.user_input, db, kwargs, resolved_intent=ctx.intent)
            
            logger.info(f"Routing to {executor.__class__.__name__} for intent {intent.intent}")

            raw_stream = executor.execute(augmented_input, intent, db=db, session_id=session_id, **kwargs)
            async for chunk in raw_stream:
                # 统一类型契约：将 StreamEvent 实体转化为字典，消除对象与字典的边界模糊 (P10 Determinism)
                if hasattr(chunk, "to_dict"):
                    chunk = chunk.to_dict()
                elif hasattr(chunk, "__dict__") and not isinstance(chunk, dict):
                    chunk = vars(chunk)
                    
                aggregator.consume(chunk)
                yield chunk

        except Exception as e:
            logger.error(f"Control Plane Pipeline Failure: {e}", exc_info=True)
            yield {"type": "error", "content": f"System orchestration error: {str(e)}"}
        finally:
            # Step 7: 非阻塞持久化 — 使用新 session 避免请求 session 关闭竞态
            # 持有 task 引用防止被 GC 提前回收
            content, reasoning, tools, stream_events = aggregator.finalize()
            if persist_assistant_message and (content or reasoning or stream_events):
                _persist_task = asyncio.create_task(self._finalize_session_safe(
                    ctx.session_id, ctx.start_time, ctx.intent, content, reasoning, tools, stream_events
                ))
                # Attach to event loop's running tasks set to survive caller scope
                asyncio.get_event_loop().call_soon(lambda: None)  # yield point ensures task is scheduled

    async def _resolve_intent(self, ctx: OrchestrationContext) -> IntentResult:
        """带强制逻辑与超时回退的意图识别"""
        mode_hint = self._get_forced_intent(ctx.kwargs)
        # P10 护城河：即使有强制模式（如 task），如果用户只是想闲聊或问问题，也应该灵活降级，避免重度执行。
        # 因此，我们将 forced 作为 mode_hint 传递给 NLU 服务，而不是直接 bypass。

        try:
            nlu_service = NluService(self.llm_model)
            # 严格限时 NLU，不能让分析影响响应速度
            return await asyncio.wait_for(
                nlu_service.analyze(
                    ctx.user_input, 
                    mode_hint=mode_hint, 
                    session_id=ctx.session_id, 
                    db=ctx.db
                ), 
                timeout=8.0
            )
        except Exception as e:
            logger.warning(f"NLU failed or timed out: {e}. Falling back safely.")
            
            fallback_intent = mode_hint or "chat"
            if not mode_hint and ctx.kwargs.get("agent_id"):
                fallback_intent = "task"
                
            return IntentResult(
                intent=fallback_intent,
                confidence=0.0,
                reasoning=f"Control plane fallback: {e}",
                parameters={},
            )

    async def _fetch_knowledge(self, ctx: OrchestrationContext) -> str:
        """多路知识获取：附件上下文 + RAG"""
        if not ctx.kwargs.get("enable_knowledge", True):
            return ""

        doc_ids = ctx.kwargs.get("doc_ids") or []
        attachment_ctx = ctx.kwargs.get("attachment_context", "")

        results = []
        if doc_ids:
            try:
                # 假设 lightrag_engine.search_chunks 已经异步化或在线程池运行
                rag_results = await asyncio.to_thread(
                    lightrag_engine.search_chunks, 
                    query=ctx.user_input, 
                    top_k=6, 
                    doc_ids=doc_ids
                )
                for r in rag_results:
                    content = r.get("content") or r.get("preview") or ""
                    results.append(f"[Source: {r.get('title', 'Unknown')}]: {content[:500]}")
            except Exception as e:
                logger.error(f"RAG Retrieval error: {e}")

        knowledge_str = "\n".join(results)
        combined = ""
        if attachment_ctx:
            combined += f"--- Attachment Content ---\n{attachment_ctx}\n"
        if knowledge_str:
            combined += f"--- Retrieved Knowledge ---\n{knowledge_str}\n"
            
        return combined[:12000] # Token 窗口安全截断

    def _build_prompt(self, ctx: OrchestrationContext) -> str:
        """构建增强提示词 (Prompt Injection)"""
        if not ctx.knowledge_fragment:
            return ctx.user_input
        
        return (
            f"Relevant Context:\n{ctx.knowledge_fragment}\n\n"
            f"User Question: {ctx.user_input}\n\n"
            f"Please answer based on the context above."
        )

    async def _init_history(self, ctx: OrchestrationContext):
        """初始化会话并保存用户消息"""
        try:
            ctx.history_manager = SessionHistory(ctx.db)
            await ctx.history_manager.ensure_session(
                ctx.session_id, 
                user_id="system_user", 
                agent_id=ctx.kwargs.get("agent_id")
            )
            if bool(ctx.kwargs.get("persist_user_message", True)):
                await ctx.history_manager.add_message(ctx.session_id, "user", ctx.user_input)
        except Exception as e:
            logger.error(f"History init failed: {e}")

    async def _finalize_session_safe(
        self,
        session_id: str,
        start_time: float,
        intent: Optional[IntentResult],
        content: str,
        reasoning: str,
        tools: List[Dict[str, Any]],
        stream_events: List[Dict[str, Any]] = None,
    ):
        """收尾工作：用独立 session 保存回复，避免与请求 session 生命周期冲突"""
        from app.db.session import AsyncSessionLocal
        duration = int((time.time() - start_time) * 1000)
        try:
            async with AsyncSessionLocal() as db:
                history = SessionHistory(db)
                meta_data = {
                    "duration_ms": duration,
                    "intent": intent.intent.value if isinstance(intent.intent, Enum) else str(intent.intent) if intent else "unknown",
                }
                if stream_events:
                    meta_data["stream_events"] = stream_events
                    
                await history.add_message(
                    session_id,
                    "assistant",
                    content,
                    reasoning_content=reasoning,
                    tool_calls=tools if tools else None,
                    meta_data=meta_data
                )
            logger.debug(f"Session {session_id} persisted in {duration}ms")
        except Exception as e:
            logger.error(f"Final persistence failed: {e}")

    async def _ensure_models(self, db: AsyncSession):
        """确保 LLM 模型已解析"""
        if not self.llm_model:
            from app.services.platform.llm.resolver import resolve_chat_llm_model
            self.llm_model = await resolve_chat_llm_model(db)

    def _get_forced_intent(self, kwargs: Dict) -> Optional[str]:
        """从请求参数中提取强制意图或模式"""
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
