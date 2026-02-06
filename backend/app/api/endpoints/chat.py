import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.crud.crud_chat import chat as crud_chat
from app.db.session import get_db
from app.models.agent import Agent
from app.models.llm_model import LLMModel
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate
from app.services.agent.manager import agent_manager
from app.services.agent.qa import qa_service  # Fallback

router = APIRouter()

# --- Sessions CRUD ---


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    return await crud_chat.get_multi(db, skip=skip, limit=limit)


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(session_in: ChatSessionCreate, db: AsyncSession = Depends(get_db)):
    return await crud_chat.create(db, session_in)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud_chat.get(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud_chat.remove(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(session_id: str, session_in: ChatSessionUpdate, db: AsyncSession = Depends(get_db)):
    session = await crud_chat.get(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return await crud_chat.update(db, session, session_in)


# --- Chat Endpoint ---


class ChatRequest(BaseModel):
    message: str
    stream: bool = True
    strict_mode: bool = False
    threshold: float = 0.85
    debug: bool = False
    ab_variant: Optional[str] = None
    attachments: Optional[List[int]] = None


@router.post("/sessions/{session_id}/chat")
async def chat_session(session_id: str, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 1. Get Session
    logger.info(f"[CHAT] Starting chat for session={session_id}")
    session = await crud_chat.get(db, session_id)
    if not session:
        logger.error(f"[CHAT] Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Save User Message
    logger.debug(f"[CHAT] User message: {request.message[:50]}...")
    user_msg = await crud_chat.create_message(db, session_id, "user", request.message)

    # 3. Get Agent
    agent = None
    agent_obj = None
    logger.info(f"[CHAT] Session agent_id={session.agent_id}")
    if session.agent_id:
        try:
            agent = await agent_manager.create_agno_agent(db, session.agent_id, session_id)
            from sqlalchemy import select

            agent_res = await db.execute(select(Agent).filter(Agent.id == session.agent_id))
            agent_obj = agent_res.scalars().first()
            logger.info(f"[CHAT] Loaded agent {session.agent_id} successfully")
        except Exception as e:
            logger.error(f"[CHAT] Failed to load agent {session.agent_id}: {e}", exc_info=True)
            pass

    # If no agent or failed, use default qa_service (global agent)
    # Note: qa_service might need model update
    target_agent_runner = None
    fallback_agent_runner = None

    if agent:
        # Detect DeepSeek first to handle history requirements
        deepseek_like = False
        try:
            # Check configured model ID string from DB
            if agent_obj and agent_obj.model_config:
                mid_conf = (agent_obj.model_config.get("model_id") or "").lower()
                if "deepseek" in mid_conf or "reasoner" in mid_conf or "r1" in mid_conf:
                    deepseek_like = True

            # Check loaded model object
            if not deepseek_like:
                model_obj = getattr(agent, "model", None)
                mid = (getattr(model_obj, "id", "") or "").lower()
                base = (getattr(model_obj, "base_url", "") or "").lower()
                deepseek_like = ("deepseek" in base) or ("deepseek" in mid) or ("reasoner" in mid) or ("r1" in mid)

            # Broader check for other providers
            if not deepseek_like and model_obj:
                provider = (getattr(model_obj, "provider", "") or "").lower()
                if "deepseek" in provider or "aliyun" in provider or "siliconflow" in provider:
                    # These providers often host DeepSeek R1
                    deepseek_like = True

            logger.info(f"[CHAT] DeepSeek detection result: {deepseek_like}")
        except Exception as e:
            logger.warning(f"[CHAT] DeepSeek detection error: {e}")
            pass

        # We need to load history into context manually if Agno agent is stateless here
        # Load history
        history_msgs = await crud_chat.get_history(db, session_id)
        logger.debug(f"[CHAT] Loaded {len(history_msgs)} history messages")

        agno_history = []
        for idx, msg in enumerate(history_msgs):
            if msg.id == user_msg.id:
                continue

            # Construct message dict
            msg_dict = {"role": msg.role, "content": msg.content}

            # Check for reasoning_content in metadata (for DeepSeek Reasoner)
            if msg.role == "assistant":
                reasoning_val = ""
                if msg.meta_data and "reasoning" in msg.meta_data and msg.meta_data["reasoning"]:
                    reasoning_val = msg.meta_data["reasoning"]

                # DeepSeek Reasoner requires reasoning_content field in history (even if empty)
                if reasoning_val:
                    msg_dict["reasoning_content"] = reasoning_val
                elif deepseek_like:
                    msg_dict["reasoning_content"] = ""

            agno_history.append(msg_dict)

        if deepseek_like:
            target_agent_runner = None
            logger.info("[CHAT] Using specialized DeepSeek/Tool runner path")
        else:
            target_agent_runner = lambda: agent.run(request.message, stream=True, messages=agno_history)
            fallback_agent_runner = lambda: [agent.run(request.message, stream=False, messages=agno_history)]
            logger.info("[CHAT] Using standard Agent runner path")

    else:
        # Legacy QA Service / Default Chat

        # Check if we failed to load a requested agent
        if session.agent_id and not agent:
            # Try to provide more specific error info
            from sqlalchemy import select

            agent_check = await db.execute(select(Agent).filter(Agent.id == session.agent_id))
            agent_obj = agent_check.scalars().first()

            error_msg = "Error: Failed to load agent."
            if agent_obj:
                has_kb = agent_obj.knowledge_config and agent_obj.knowledge_config.get("document_ids")
                from app.services.agent.manager import has_global_api_key

                if has_kb and not has_global_api_key():
                    error_msg += (
                        " Knowledge Base requires global OpenAI API Key (OPENAI_API_KEY) or compatible embedding model."
                    )
                else:
                    error_msg += " Please check agent configuration (Model/Knowledge)."
            else:
                error_msg += " Agent not found."

            logger.error(f"[CHAT] Agent load failure: {error_msg}")
            return StreamingResponse(iter([error_msg]), media_type="text/plain")

        # No agent selected, try to use a default active model safely (No Singleton)
        logger.info("[CHAT] No agent selected, attempting to use default active model")

        # 1. Find active model
        from sqlalchemy import select

        res = await db.execute(
            select(LLMModel)
            .filter(LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
            .order_by(LLMModel.updated_at.desc())
        )
        active_model = res.scalars().first()

        if active_model:
            logger.info(f"[CHAT] Found default active model: {active_model.model_id}")

            # 2. Create Temporary Agent (Local Scope, No Singleton)
            from agno.agent import Agent as AgnoAgent

            from app.services.llm.factory import ModelFactory

            try:
                # Use ModelFactory to create the model instance (handles provider specifics)
                model_instance = ModelFactory.create_model(active_model)
                is_reasoning = ModelFactory.should_use_agno_reasoning(active_model)
                is_native_reasoning = ModelFactory.is_reasoning_model(active_model)

                # Instantiate a fresh agent for this request
                temp_agent = AgnoAgent(
                    name="Default Agent",
                    model=model_instance,
                    instructions="You are a helpful assistant.",
                    markdown=True,
                    reasoning=is_reasoning,
                    # show_reasoning=True # Avoid TypeError in some versions
                )

                # 3. Detect DeepSeek Logic (Reused)
                deepseek_like = False
                active_mid = (active_model.model_id or "").lower()
                active_base = (active_model.base_url or "").lower()
                active_provider = (active_model.provider or "").lower()
                if "deepseek" in active_mid or "reasoner" in active_mid or "r1" in active_mid:
                    deepseek_like = True
                elif "deepseek" in active_base or "deepseek" in active_provider:
                    deepseek_like = True
                elif "aliyun" in active_provider or "siliconflow" in active_provider:
                    deepseek_like = True

                logger.info(f"[CHAT] Default agent DeepSeek detection: {deepseek_like}")

                # 4. Load History Manually
                history_msgs = await crud_chat.get_history(db, session_id)
                logger.debug(f"[CHAT] Loaded {len(history_msgs)} history messages for default agent")

                agno_history = []
                for idx, msg in enumerate(history_msgs):
                    if msg.id == user_msg.id:
                        continue
                    msg_dict = {"role": msg.role, "content": msg.content}
                    if msg.role == "assistant":
                        reasoning_val = ""
                        if msg.meta_data and "reasoning" in msg.meta_data and msg.meta_data["reasoning"]:
                            reasoning_val = msg.meta_data["reasoning"]
                        if reasoning_val:
                            msg_dict["reasoning_content"] = reasoning_val
                        elif deepseek_like:
                            msg_dict["reasoning_content"] = ""
                    agno_history.append(msg_dict)

                target_agent_runner = lambda: temp_agent.run(request.message, stream=True, messages=agno_history)
                fallback_agent_runner = lambda: [temp_agent.run(request.message, stream=False, messages=agno_history)]

                agent = temp_agent

            except Exception as e:
                logger.error(f"[CHAT] Failed to create default agent: {e}", exc_info=True)
                return StreamingResponse(
                    iter([f"Error: Failed to initialize default agent: {str(e)}"]), media_type="text/plain"
                )
        else:
            # If no active model found, check if we have global key (Fallback to bare OpenAI)
            from app.services.agent.manager import has_global_api_key

            if has_global_api_key():
                logger.info("[CHAT] No active model found, falling back to global OpenAI key")
                # We can use qa_service here as a last resort OR create a fresh OpenAI agent.
                # Let's create a fresh one to be consistent.
                from agno.agent import Agent as AgnoAgent
                from agno.models.openai import OpenAIChat

                from app.core.config import settings

                temp_agent = AgnoAgent(
                    name="Global Default Agent",
                    model=OpenAIChat(id="gpt-4o", api_key=settings.OPENAI_API_KEY),
                    instructions="You are a helpful assistant.",
                    markdown=True,
                )

                # Default history (no DeepSeek fix needed)
                history_msgs = await crud_chat.get_history(db, session_id)
                agno_history = [{"role": m.role, "content": m.content} for m in history_msgs if m.id != user_msg.id]

                target_agent_runner = lambda: temp_agent.run(request.message, stream=True, messages=agno_history)
                fallback_agent_runner = lambda: [temp_agent.run(request.message, stream=False, messages=agno_history)]
            else:
                logger.warning("[CHAT] No active model and no global key")
                return StreamingResponse(
                    iter(["Error: No active model found. Please configure a model in Settings."]),
                    media_type="text/plain",
                )

    # 4. Stream Response & Save Assistant Message
    async def event_generator():
        full_response = ""
        reasoning_content = ""
        references = []
        filtered_out = []
        retrieval_note = None
        strict_enabled = False

        try:
            allowed_names = []
            doc_ids = []

            # 1. Agent bound docs
            if agent_obj and agent_obj.knowledge_config:
                doc_ids = list(agent_obj.knowledge_config.get("document_ids") or [])

            # 2. Request attachments
            if request.attachments:
                doc_ids.extend(request.attachments)

            doc_ids = list(set(doc_ids))

            if doc_ids:
                from sqlalchemy import select

                from app.models.knowledge import KnowledgeDocument

                docs_res = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id.in_(doc_ids)))
                docs = docs_res.scalars().all()
                allowed_names = [d.filename for d in docs if d and d.filename]

            strict_enabled = bool(
                request.strict_mode
                or (agent_obj and agent_obj.knowledge_config and agent_obj.knowledge_config.get("strict_only"))
            )

            if strict_enabled and allowed_names:
                retrieval_note = "根据绑定文档检索"

            from app.services.rag.knowledge_base import kb_service

            try:
                if hasattr(kb_service, "search"):
                    import asyncio
                    refs, filtered = await asyncio.to_thread(
                        kb_service.search,
                        query=request.message,
                        allowed_names=allowed_names if strict_enabled else None,
                        min_score=request.threshold if request.threshold is not None else 0.85,
                        top_k=5,
                    )
                else:
                    refs, filtered = [], []
                references = refs or []
                filtered_out = filtered or []
                logger.info(
                    f"Retrieval strict={strict_enabled} allowed={len(allowed_names)} refs={len(references)} filtered={len(filtered_out)}"
                )
            except Exception as se:
                logger.warning(f"Retrieval failed: {se}")

            structured_refs = []
            if references:
                try:
                    titles = [r.get("title") for r in references if r.get("title")]
                    if titles:
                        from sqlalchemy import select

                        from app.models.knowledge import KnowledgeDocument

                        docs_res = await db.execute(
                            select(KnowledgeDocument).filter(KnowledgeDocument.filename.in_(titles))
                        )
                        docs_list = docs_res.scalars().all()
                        idx = {d.filename: d for d in docs_list}
                    else:
                        idx = {}
                    for r in references:
                        t = r.get("title") or ""
                        d = idx.get(t)
                        structured_refs.append(
                            {
                                "id": d.id if d else 0,
                                "title": t,
                                "createTime": (d.created_at.isoformat() if d and d.created_at else None),
                                "coverImage": (d.oss_url if d else r.get("url")),
                                "summary": r.get("preview") or "",
                                "tags": [],
                            }
                        )
                except Exception as re:
                    logger.warning(f"Failed to build structured references: {re}")

            if target_agent_runner:
                try:
                    stream = target_agent_runner()
                except Exception as e:
                    err_msg = str(e)
                    # Check for Aliyun/DeepSeek specific errors (1210: Invalid Param, 1212: SSE not supported)
                    if ("1212" in err_msg or "SSE" in err_msg or "1210" in err_msg) and fallback_agent_runner:
                        logger.warning(f"Streaming failed ({err_msg}), attempting fallback to non-streaming.")
                        stream = fallback_agent_runner()
                    else:
                        raise e
            else:
                try:
                    from app.services.agent.tools.runner import run_reasoning_tool_loop
                    from app.services.agent.tools.duckduckgo import DuckDuckGoTools

                    model_obj = getattr(agent, "model", None)
                    api_key = getattr(model_obj, "api_key", None) or ""
                    base_url = getattr(model_obj, "base_url", None)
                    model_id = getattr(model_obj, "id", None) or "deepseek-reasoner"
                    client = OpenAI(api_key=api_key or "dummy", base_url=base_url)
                    ddg = DuckDuckGoTools()
                    tools = [
                        {
                            "type": "function",
                            "function": {
                                "name": "duckduckgo_search",
                                "description": "Search the web using DuckDuckGo",
                                "parameters": {
                                    "type": "object",
                                    "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}},
                                    "required": ["query"],
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "get_datetime",
                                "description": "Get current datetime string",
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                },
                            },
                        },
                    ]

                    def _get_datetime():
                        from datetime import datetime

                        return {"now": datetime.now().isoformat()}

                    tool_map = {
                        "duckduckgo_search": lambda query, max_results=5: (
                            json.loads(ddg.search(query, max_results=max_results))
                            if ddg
                            else {"error": "ddg not available"}
                        ),
                        "get_datetime": lambda: _get_datetime(),
                    }

                    # Only enable thinking for DeepSeek Reasoner models
                    is_deepseek = "deepseek" in model_id.lower() and (
                        "reasoner" in model_id.lower() or "r1" in model_id.lower()
                    )

                    res = run_reasoning_tool_loop(
                        client=client,
                        model_id=model_id,
                        user_prompt=request.message,
                        tools=tools,
                        tool_call_map=tool_map,
                        enable_thinking=is_deepseek,
                        messages=agno_history,  # Pass history
                    )
                    final_msg = res["final_message"]
                    rc = getattr(final_msg, "reasoning_content", None) or None
                    if rc:
                        reasoning_content += rc
                        yield "<think>\n"
                        yield rc
                        yield "\n</think>\n"
                    content_text = getattr(final_msg, "content", "") or ""
                    full_response += content_text
                    yield content_text
                    stream = []
                except Exception as ee:
                    logger.error(f"DeepSeek tool loop error: {ee}")
                    stream = []

            has_started_reasoning = False
            has_ended_reasoning = False

            for response in stream:
                content_chunk = ""
                reasoning_chunk = ""

                # Extract reasoning
                if hasattr(response, "reasoning_content") and response.reasoning_content:
                    reasoning_chunk = response.reasoning_content
                elif hasattr(response, "response_delta") and response.response_delta:
                    delta = response.response_delta
                    if hasattr(delta, "reasoning_content"):
                        reasoning_chunk = delta.reasoning_content
                    elif isinstance(delta, dict) and "reasoning_content" in delta:
                        reasoning_chunk = delta["reasoning_content"]

                # Handle reasoning tags
                if reasoning_chunk:
                    reasoning_content += reasoning_chunk
                    if not has_started_reasoning:
                        yield "<think>\n"
                        has_started_reasoning = True
                    yield reasoning_chunk

                # Extract content
                if hasattr(response, "content") and response.content:
                    content_chunk = response.content
                elif hasattr(response, "delta") and response.delta:
                    content_chunk = response.delta
                elif isinstance(response, str):
                    content_chunk = response

                # Agno's RunResponse might wrap content differently
                if not content_chunk and hasattr(response, "response_delta") and response.response_delta:
                    delta = response.response_delta
                    if isinstance(delta, str):
                        content_chunk = delta
                    elif hasattr(delta, "content"):
                        content_chunk = delta.content

                if content_chunk:
                    # Close reasoning if needed
                    if has_started_reasoning and not has_ended_reasoning:
                        yield "\n</think>\n"
                        has_ended_reasoning = True

                    full_response += content_chunk
                    yield content_chunk

            # Close reasoning if ended without content
            if has_started_reasoning and not has_ended_reasoning:
                yield "\n</think>\n"

            if references:
                citations = ["\n\nReferences:"]
                for i, r in enumerate(references, 1):
                    title = r.get("title") or ""
                    url = r.get("url") or ""
                    page = r.get("page")
                    score = r.get("score")
                    preview = r.get("preview") or ""
                    line = f"{i}. {title}"
                    if page is not None:
                        line += f" (page {page})"
                    if url:
                        line += f" - {url}"
                    if score is not None:
                        line += f" [score {score:.2f}]"
                    citations.append(line)
                    if preview:
                        citations.append(f"   Preview: {preview}")
                citations_text = "\n".join(citations) + "\n"
                full_response += citations_text
                yield citations_text

            # 5. Save Assistant Message to DB
            meta = {}
            if reasoning_content:
                meta["reasoning"] = reasoning_content
            if references:
                meta["references"] = references
            if structured_refs:
                meta["structured_references"] = structured_refs
            if request.debug and filtered_out:
                meta["filtered_out"] = filtered_out
            if retrieval_note:
                meta["retrieval_note"] = retrieval_note
            if strict_enabled:
                meta["strict_mode"] = True
            if request.ab_variant:
                meta["ab_variant"] = request.ab_variant

            await save_assistant_message(
                session_id, full_response, None if not meta.get("reasoning") else meta["reasoning"]
            )
            if meta:
                await save_message_meta(session_id, meta)

        except Exception as e:
            msg = str(e)
            if "Missing reasoning_content field" in msg:
                logger.error(
                    "DeepSeek Thinking Mode error: assistant message缺少reasoning_content。已在历史构造阶段进行自动补全，请检查本次对话内的工具调用环节是否正确回传reasoning_content。"
                )
            elif "401" in msg or "authentication" in msg.lower():
                # Try to extract model info to help user debug
                model_info = "Unknown"
                try:
                    if agent and hasattr(agent, "model"):
                        m = agent.model
                        model_info = f"ID={getattr(m, 'id', 'N/A')}, BaseURL={getattr(m, 'base_url', 'N/A')}"
                    elif active_model:
                        model_info = f"ID={active_model.model_id}, BaseURL={active_model.base_url}"
                except:
                    pass
                logger.error(f"Authentication failed for model {model_info}: {e}")
                yield f"Error: Authentication failed (401). Please check API Key for model [{model_info}]. Details: {msg}"
            else:
                logger.error(f"Chat error: {e}")
                yield f"Error: {str(e)}"

    return StreamingResponse(event_generator(), media_type="text/plain")


async def save_assistant_message(session_id: str, content: str, reasoning: str = None):
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await crud_chat.create_message(
                db, session_id, "assistant", content, {"reasoning": reasoning} if reasoning else None
            )
        except Exception as e:
            logger.error(f"Failed to save assistant message: {e}")


async def save_message_meta(session_id: str, meta: dict):
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await crud_chat.update_message_meta(db, session_id, meta)
        except Exception as e:
            logger.error(f"Failed to update assistant message meta: {e}")


# Legacy endpoint (keep for compatibility if needed, or redirect)
@router.post("/completions")
async def chat_completions(request: ChatRequest):
    return StreamingResponse(qa_service.chat_stream(request.message), media_type="text/plain")
