"""
Agno Control Plane
智能体控制平面
功能：
- 接收前端消息
- 解析意图
- 路由到对应的处理模块
- 整合处理结果
- 发送回前端
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, AsyncGenerator

from app.core.config import settings
from app.core.i18n import _
from app.services.eah_agent.core.nlu import NluService, IntentResult
from app.services.eah_agent.core.stream_normalizer import normalize_event_stream
from app.services.openclaw.clients.agno import AgnoGatewayClient
from app.models.llm_model import LLMModel
from app.services.eah_agent.storage.session_history import SessionHistory
from app.services.rag.retrieval.engines.lightrag import lightrag_engine
from sqlalchemy.ext.asyncio import AsyncSession

# Handlers
from app.services.eah_agent.handlers.quick_handler import QuickHandler
from app.services.eah_agent.handlers.plan_handler import PlanHandler
from app.services.eah_agent.handlers.team_handler import TeamHandler
from app.services.eah_agent.handlers.flow_handler import FlowHandler
from app.services.eah_agent.handlers.data_handler import DataHandler

logger = logging.getLogger("agno.control_plane")

class AgnoControlPlane:
    """
    Agno Intelligent Agent as the sole control plane.
    Refactored to dispatch to specialized handlers.
    """

    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model
        self.nlu = NluService(llm_model)
        
        # Initialize Handlers
        self.quick_handler = QuickHandler(llm_model)
        self.plan_handler = PlanHandler(llm_model)
        self.team_handler = TeamHandler(llm_model)
        self.flow_handler = FlowHandler(llm_model)
        self.data_handler = DataHandler(llm_model)
        
        # Initialize WS Client
        # Using settings or defaults
        gateway_url = settings.OPENCLAW_WS_URL or "ws://localhost:8000"
        api_key = getattr(settings, "OPENCLAW_AGNO_KEY", "test-key")
        api_secret = getattr(settings, "OPENCLAW_AGNO_SECRET", "test-secret")
        
        self.client = AgnoGatewayClient(
            gateway_url=gateway_url,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Register callbacks
        self.client.on_task_event = self._on_task_event

    async def start(self):
        """Starts the control plane (connects to gateway)."""
        await self.client.connect()

    async def stop(self):
        """Stops the control plane."""
        await self.client.close()

    async def process_stream(self, user_input: str, db: Optional[AsyncSession] = None, session_id: Optional[str] = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        New main entry point supporting streaming.
        Dispatches to handlers based on NLU intent.
        """
        if not self.llm_model and db:
            from app.services.llm.resolver import resolve_chat_llm_model, resolve_fast_llm_model

            self.llm_model = await resolve_chat_llm_model(db)
            
            # 使用统一的快速模型解析器为 NLU 选择一个轻量级模型
            nlu_model = await resolve_fast_llm_model(db) or self.llm_model
            
            if nlu_model and self.llm_model and nlu_model.model_id != self.llm_model.model_id:
                logger.info(f"Using fast model {nlu_model.model_id} for NLU instead of {self.llm_model.model_id}")

            self.nlu = NluService(nlu_model)
            for h in (
                self.quick_handler,
                self.plan_handler,
                self.team_handler,
                self.flow_handler,
                self.data_handler,
            ):
                if getattr(h, "llm_model", None) != self.llm_model:
                    setattr(h, "llm_model", self.llm_model)
                    if hasattr(h, "agent"):
                        setattr(h, "agent", None)

        requested_mode = kwargs.get("mode")
        requested_intent = kwargs.get("intent_override") or kwargs.get("intent")

        threshold = kwargs.get("threshold", 0.85)
        try:
            threshold = float(threshold)
        except Exception:
            threshold = 0.85

        forced_intent = None
        if isinstance(requested_intent, str) and requested_intent.strip():
            forced_intent = requested_intent.strip().lower()
        elif isinstance(requested_mode, str) and requested_mode.strip():
            mode = requested_mode.strip().lower()
            if mode in {"quick", "chat"}:
                # 只有 Quick/Chat 模式才需要 NLU 分析（或者 forced_intent=None 让其走下面的 else 分支）
                # 这里显式设置为 None，让其进入 NLU 流程
                forced_intent = None
            elif mode in {"solo", "plan", "task"}:
                forced_intent = "task"
            elif mode in {"team"}:
                forced_intent = "team"
            elif mode in {"workflow", "flow"}:
                forced_intent = "workflow"
            elif mode in {"data_query", "data"}:
                forced_intent = "data_query"
            elif mode in {"kg_qa", "kgqa", "kg"}:
                forced_intent = "kg_qa"

        result: Optional[IntentResult] = None
        
        # 0. Early Feedback & Parallel Execution Setup
        yield {"type": "status", "content": _("Processing...")}
        
        rag_future = None
        
        # Start RAG early if needed
        bool(kwargs.get("enable_search", True))
        enable_knowledge = bool(kwargs.get("enable_knowledge", True))
        raw_doc_ids = kwargs.get("doc_ids") or []
        doc_ids = []
        if isinstance(raw_doc_ids, (list, tuple)):
            for x in raw_doc_ids:
                try:
                    if x is None:
                        continue
                    if isinstance(x, int):
                        doc_ids.append(x)
                        continue
                    s = str(x).strip()
                    if s.isdigit():
                        doc_ids.append(int(s))
                except Exception:
                    continue
        
        attachment_context = kwargs.get("attachment_context")
        
        if enable_knowledge and doc_ids:
             # Start RAG in background
             rag_future = asyncio.create_task(asyncio.to_thread(lightrag_engine.search_chunks, query=user_input, top_k=6, doc_ids=doc_ids))

        # 1. Intent Analysis
        if forced_intent in {"chat", "team", "workflow", "data_query", "kg_qa", "task"}:
            result = IntentResult(intent=forced_intent, confidence=1.0, task_params=None)
        else:
            try:
                yield {"type": "status", "content": _("Analyzing intent...")}
                # Set a timeout for NLU analysis to prevent long waits, especially if using a reasoning model
                try:
                    result = await asyncio.wait_for(self.nlu.analyze(user_input), timeout=8.0)
                    logger.info(f"Intent Analysis: {result}")
                except asyncio.TimeoutError:
                    logger.warning("NLU Analysis timed out after 8s. Falling back to 'chat' intent.")
                    result = IntentResult(intent="chat", confidence=0.0)
            except Exception as e:
                logger.error(f"NLU Analysis failed: {e}")
                yield {"type": "error", "content": _("I couldn't understand that.")}
                return

        # 2. Session Persistence (Save User Message)
        history = None
        if db and session_id:
            try:
                history = SessionHistory(db)
                # Check if session exists, if not create
                session = await history.get_session(session_id)
                if not session:
                    # In a real app, user_id should come from auth context
                    await history.create_session(user_id="guest", agent_id=None, title=user_input[:50])
                
                # Async add message without blocking the main flow too much? 
                # Actually, await is fine as it's usually fast, but we can parallelize with RAG if needed.
                await history.add_message(session_id, "user", user_input)
            except Exception as e:
                logger.error(f"Failed to save user message: {e}")

        # 3. RAG Result Retrieval
        augmented_input = user_input
        
        if attachment_context or (enable_knowledge and doc_ids):
            yield {"type": "status", "content": _("Retrieving knowledge...")}
            parts = []
            if attachment_context:
                parts.append("【用户上传/选择的附件内容（提取结果）】\n" + str(attachment_context))
            
            results = []
            if rag_future:
                try:
                    results = await rag_future
                except Exception as e:
                    logger.error(f"RAG search failed: {e}")
                    results = []
            
            if results:
                    lines = []
                    for r in results:
                        title = r.get("title") or ""
                        did = r.get("doc_id")
                        preview = (r.get("content") or r.get("preview") or "").strip()
                        if len(preview) > 600:
                            preview = preview[:600]
                        head = f"- doc#{did}:{title}" if did is not None else f"- {title}"
                        lines.append(head + ("\n" + preview if preview else ""))
                    parts.append("【仅在附件范围内的相关检索摘录】\n" + "\n\n".join(lines))
            prefix = "\n\n".join([p for p in parts if p]).strip()
            if prefix:
                if len(prefix) > 8000:
                    prefix = prefix[:8000]
                augmented_input = prefix + "\n\n【用户问题】\n" + user_input

        # 3. Dispatch & Stream
        full_response = ""
        full_reasoning = ""
        start_time = time.time()
        
        try:
            handler_stream = None
            
            if result.intent == "chat" or result.confidence < threshold:
                handler_stream = self.quick_handler.process(augmented_input, result, db=db, session_id=session_id, **kwargs)
            elif result.intent == "task":
                # Use PlanHandler for all task intents (both forced Solo/Plan mode and NLU detected tasks)
                handler_stream = self.plan_handler.process(augmented_input, result, db=db, session_id=session_id, **kwargs)
            elif result.intent == "team":
                 handler_stream = self.team_handler.process(augmented_input, result, db=db, session_id=session_id, **kwargs)
            elif result.intent == "workflow":
                 handler_stream = self.flow_handler.process(augmented_input, result, db=db, session_id=session_id, **kwargs)
            elif result.intent == "data_query" or result.intent == "kg_qa":
                 handler_stream = self.data_handler.process(augmented_input, result, db=db, session_id=session_id, **kwargs)
            else:
                handler_stream = self.quick_handler.process(augmented_input, result, db=db, session_id=session_id, **kwargs)
            
            if handler_stream:
                async for chunk in normalize_event_stream(handler_stream):
                    if chunk.get("type") == "content":
                        content = chunk.get("content")
                        if isinstance(content, str):
                            full_response += content
                    elif chunk.get("type") == "think":
                        content = chunk.get("content")
                        if isinstance(content, str):
                            full_reasoning += content
                    yield chunk

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            yield {"type": "error", "content": _("An error occurred during processing.")}
            full_response += "\n[Error occurred]"
        
        # 4. Session Persistence (Save Assistant Message)
        if history and session_id and full_response:
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            meta_data = {"duration": duration_ms}
            if full_reasoning:
                meta_data["reasoning"] = full_reasoning
            try:
                await history.add_message(session_id, "assistant", full_response, meta_data=meta_data)
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")

    async def process_input(self, user_input: str) -> str:
        """
        Legacy entry point for backward compatibility.
        Consumes the stream and returns full string.
        """
        full_response = ""
        try:
            async for chunk in self.process_stream(user_input):
                if chunk.get("type") == "content":
                    full_response += str(chunk.get("content", ""))
                elif chunk.get("type") == "error":
                    full_response += f"\n[Error: {chunk.get('content')}]"
        except Exception as e:
            logger.error(f"Process input failed: {e}")
            return _("An error occurred.")
            
        return full_response

    async def _handle_task(self, params: Dict[str, Any]) -> str:
        if not self.client.is_connected:
            # Auto-connect if not connected
            await self.start()
            if not self.client.is_connected:
                 return _("Service temporarily unavailable (Gateway disconnected).")

        task_type = params.get("task_type")
        target = params.get("target")
        timeout = params.get("timeout", 60)
        retry_policy = params.get("retry_policy")

        try:
            # Blocking wait for task execution
            event = await self.client.execute_task(
                task_type=task_type,
                target=target,
                payload=params, # Pass all params as payload
                timeout=timeout,
                retry_policy=retry_policy
            )
            
            method = event.get("method")
            if method == "task_completed":
                return _("Task completed successfully: {}").format(event.get('params', {}).get('result'))
            elif method == "task_failed":
                error = event.get('params', {}).get('error', {})
                code = error.get('code')
                msg = error.get('message')
                # Auto-retry logic could be here if not handled by gateway, 
                # but requirement says "agno auto parses error_code, decides retry or human"
                return _("Task failed (Code {}): {}").format(code, msg)
            else:
                return _("Task finished with status: {}").format(method)

        except TimeoutError:
            return _("Task execution timed out.")
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            return _("An error occurred while executing the task: {}").format(str(e))

    async def _on_task_event(self, event: Dict):
        """
        Callback for async events from Gateway.
        Updates session context or logs.
        """
        method = event.get("method")
        params = event.get("params", {})
        task_id = params.get("task_id")
        
        logger.info(f"Received event {method} for task {task_id}")
        # Here we could update a database or persistent session state
