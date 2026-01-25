from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
import logging
import json
from openai import OpenAI

from app.db.session import get_db
from app.models.chat import ChatSession, ChatMessage
from app.models.agent import Agent
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatMessageCreate, ChatSessionUpdate
from app.services.agent_manager import agent_manager
from app.services.qa_agent import qa_service # Fallback

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Sessions CRUD ---

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    query = select(ChatSession).options(selectinload(ChatSession.messages)).order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    session_in: ChatSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    new_session = ChatSession(
        title=session_in.title or "New Chat",
        agent_id=session_in.agent_id
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Ensure messages is initialized for Pydantic response
    # Even though it's empty, Pydantic might try to access it if defined in response model
    # And since it's a relationship, it might trigger lazy load if not careful
    # But since we just created it, it should be fine or empty list
    # Let's explicitly set it to empty list to be safe from async lazy load error
    # new_session.messages = [] 
    
    # Actually, the error might be because refresh loads attributes but relationship remains unloaded
    # and then Pydantic tries to access .messages which triggers async lazy load error.
    # We can eager load it or set it manually.
    
    # Let's re-fetch it properly or just set .messages = []
    # Re-fetching is safer
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .filter(ChatSession.id == new_session.id)
    )
    session = result.scalars().first()
    return session

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Fetch session with messages eager loaded
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .filter(ChatSession.id == session_id)
    )
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()
    return {"status": "deleted"}

@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: str,
    session_in: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ChatSession).options(selectinload(ChatSession.messages)).filter(ChatSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_in.title is not None:
        session.title = session_in.title
        
    if session_in.agent_id is not None:
        session.agent_id = session_in.agent_id
        
    await db.commit()
    await db.refresh(session)
    # Ensure messages relationship is loaded to satisfy response model
    # Since refresh might unload relationships, and we used selectinload above,
    # accessing session.messages should be fine if it was eagerly loaded.
    # However, sometimes refresh clears it. Safe bet is to re-query if needed or rely on session being attached.
    # But let's check if session.messages is accessible.
    
    return session

# --- Chat Endpoint ---

class ChatRequest(BaseModel):
    message: str
    stream: bool = True
    strict_mode: bool = False
    threshold: float = 0.85
    debug: bool = False
    ab_variant: str | None = None
    attachments: Optional[List[int]] = None

from app.models.llm_model import LLMModel

@router.post("/sessions/{session_id}/chat")
async def chat_session(
    session_id: str,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Get Session
    logger.info(f"[CHAT] Starting chat for session={session_id}")
    result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id))
    session = result.scalars().first()
    if not session:
        logger.error(f"[CHAT] Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Save User Message
    logger.debug(f"[CHAT] User message: {request.message[:50]}...")
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    await db.commit()

    # 3. Get Agent
    agent = None
    agent_obj = None
    logger.info(f"[CHAT] Session agent_id={session.agent_id}")
    if session.agent_id:
        try:
            agent = await agent_manager.create_agno_agent(db, session.agent_id, session_id)
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
        history_res = await db.execute(
            select(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        history_msgs = history_res.scalars().all()
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
        
        # (Verification logic removed as it was overly aggressive for history messages)
        
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
             # It might fail because of KB configuration (missing OpenAI Key) even if Model is valid
             # Or model is invalid.
             # Since we are inside the endpoint, we can check specific conditions
             
             # Check if agent exists
             agent_check = await db.execute(select(Agent).filter(Agent.id == session.agent_id))
             agent_obj = agent_check.scalars().first()
             
             error_msg = "Error: Failed to load agent."
             if agent_obj:
                 has_kb = agent_obj.knowledge_config and agent_obj.knowledge_config.get("document_ids")
                 from app.services.agent_manager import has_global_api_key
                 if has_kb and not has_global_api_key():
                     error_msg += " Knowledge Base requires global OpenAI API Key (OPENAI_API_KEY) or compatible embedding model."
                 else:
                     error_msg += " Please check agent configuration (Model/Knowledge)."
             else:
                 error_msg += " Agent not found."

             logger.error(f"[CHAT] Agent load failure: {error_msg}")
             return StreamingResponse(
                 iter([error_msg]), 
                 media_type="text/plain"
             )
        
        # No agent selected, try to use a default active model safely (No Singleton)
        logger.info("[CHAT] No agent selected, attempting to use default active model")
        
        # 1. Find active model
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
            from app.services.model_factory import ModelFactory
            
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
                history_res = await db.execute(
                    select(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc())
                )
                history_msgs = history_res.scalars().all()
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
                
                # 5. Define Runners
                # Note: AgnoAgent.run() is synchronous or async depending on implementation, 
                # but typically in this codebase it seems to be treated as sync or wrapped.
                # However, previous code used `agent.run(stream=True)`.
                
                target_agent_runner = lambda: temp_agent.run(request.message, stream=True, messages=agno_history)
                fallback_agent_runner = lambda: [temp_agent.run(request.message, stream=False, messages=agno_history)]
                
                # Set agent_obj to None since we don't have a DB agent
                agent = temp_agent # For logic below that checks `if agent:` (Wait, logic below checks `if agent:` block which we skipped)
                # Actually, the logic below `if agent:` block (lines 177-241) was skipped because `agent` was None.
                # Now we are in `else`. We defined `target_agent_runner`.
                # We need to ensure `agent` variable is set if we want `event_generator` to use it?
                # `event_generator` checks `agent_obj` for docs. `agent_obj` is None.
                # It checks `agent` for nothing specific except passed to KB search? No.
                
                # Just setting target_agent_runner is enough for `event_generator` to work.
                
            except Exception as e:
                logger.error(f"[CHAT] Failed to create default agent: {e}", exc_info=True)
                return StreamingResponse(
                    iter([f"Error: Failed to initialize default agent: {str(e)}"]), 
                    media_type="text/plain"
                )
        else:
            # If no active model found, check if we have global key (Fallback to bare OpenAI)
            from app.services.agent_manager import has_global_api_key
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
                    markdown=True
                 )
                 
                 # Default history (no DeepSeek fix needed)
                 history_res = await db.execute(
                    select(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc())
                )
                 history_msgs = history_res.scalars().all()
                 agno_history = [{"role": m.role, "content": m.content} for m in history_msgs if m.id != user_msg.id]
                 
                 target_agent_runner = lambda: temp_agent.run(request.message, stream=True, messages=agno_history)
                 fallback_agent_runner = lambda: [temp_agent.run(request.message, stream=False, messages=agno_history)]
            else:
                 logger.warning("[CHAT] No active model and no global key")
                 return StreamingResponse(
                     iter([f"Error: No active model found. Please configure a model in Settings."]), 
                     media_type="text/plain"
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
                from app.models.knowledge import KnowledgeDocument
                docs_res = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id.in_(doc_ids)))
                docs = docs_res.scalars().all()
                allowed_names = [d.filename for d in docs if d and d.filename]
            
            strict_enabled = bool(request.strict_mode or (agent_obj and agent_obj.knowledge_config and agent_obj.knowledge_config.get("strict_only")))
            # If we have attachments, we implicitly enable strict/filtering logic if strict mode is ON
            # But actually, if user uploads attachment, they expect it to be used. 
            # If strict mode is OFF, we search everything.
            # If strict mode is ON, we only search allowed_names.
            # With attachments, allowed_names now includes attachments.
            
            if strict_enabled and allowed_names:
                retrieval_note = "根据绑定文档检索"
            if agent:
                pass
            from app.services.knowledge_base import kb_service
            try:
                if hasattr(kb_service, "search"):
                    refs, filtered = kb_service.search(
                        query=request.message,
                        allowed_names=allowed_names if strict_enabled else None,
                        min_score=request.threshold if request.threshold is not None else 0.85,
                        top_k=5
                    )
                else:
                    raw = kb_service.vector_db.search(request.message, limit=5)
                    refs = []
                    filtered = []
                    thr = request.threshold if request.threshold is not None else 0.85
                    for r in raw:
                        meta = getattr(r, "metadata", {}) if hasattr(r, "metadata") else (r.get("metadata") if isinstance(r, dict) else {})
                        name = (meta or {}).get("name") or (meta or {}).get("filename") or (getattr(r, "name", None) if hasattr(r, "name") else (r.get("name") if isinstance(r, dict) else None))
                        score = getattr(r, "score", 0.0) if hasattr(r, "score") else (r.get("score", 0.0) if isinstance(r, dict) else 0.0)
                        content = getattr(r, "content", None) if hasattr(r, "content") else (r.get("content") if isinstance(r, dict) else None)
                        if strict_enabled and allowed_names and name and name not in allowed_names:
                            filtered.append({"title": name, "score": score})
                            continue
                        if score is not None and score < thr:
                            filtered.append({"title": name, "score": score})
                            continue
                        refs.append({
                            "title": name or "",
                            "url": (meta or {}).get("url"),
                            "page": (meta or {}).get("page"),
                            "score": score,
                            "preview": (content or (meta or {}).get("text") or "")[:200]
                        })
                references = refs or []
                filtered_out = filtered or []
                logger.info(f"Retrieval strict={strict_enabled} allowed={len(allowed_names)} refs={len(references)} filtered={len(filtered_out)}")
            except Exception as se:
                logger.warning(f"Retrieval failed: {se}")
            
            structured_refs = []
            if references:
                try:
                    titles = [r.get("title") for r in references if r.get("title")]
                    if titles:
                        from app.models.knowledge import KnowledgeDocument
                        docs_res = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.filename.in_(titles)))
                        docs_list = docs_res.scalars().all()
                        idx = {d.filename: d for d in docs_list}
                    else:
                        idx = {}
                    for r in references:
                        t = r.get("title") or ""
                        d = idx.get(t)
                        structured_refs.append({
                            "id": d.id if d else 0,
                            "title": t,
                            "createTime": (d.created_at.isoformat() if d and d.created_at else None),
                            "coverImage": (d.oss_url if d else r.get("url")),
                            "summary": r.get("preview") or "",
                            "tags": []
                        })
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
                    from app.services.tool_runner import run_reasoning_tool_loop
                    from app.services.tools.duckduckgo import DuckDuckGoTools
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
                                    "properties": {
                                        "query": {"type": "string"},
                                        "max_results": {"type": "integer"}
                                    },
                                    "required": ["query"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "get_datetime",
                                "description": "Get current datetime string",
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                }
                            }
                        }
                    ]
                    def _get_datetime():
                        from datetime import datetime
                        return {"now": datetime.now().isoformat()}
                    tool_map = {
                        "duckduckgo_search": lambda query, max_results=5: json.loads(ddg.search(query, max_results=max_results)) if ddg else {"error": "ddg not available"},
                        "get_datetime": lambda: _get_datetime()
                    }
                    
                    # Only enable thinking for DeepSeek Reasoner models
                    is_deepseek = "deepseek" in model_id.lower() and ("reasoner" in model_id.lower() or "r1" in model_id.lower())
                    
                    res = run_reasoning_tool_loop(
                        client=client,
                        model_id=model_id,
                        user_prompt=request.message,
                        tools=tools,
                        tool_call_map=tool_map,
                        enable_thinking=is_deepseek,
                        messages=agno_history # Pass history
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
                if hasattr(response, 'reasoning_content') and response.reasoning_content:
                    reasoning_chunk = response.reasoning_content
                elif hasattr(response, 'response_delta') and response.response_delta:
                    delta = response.response_delta
                    if hasattr(delta, 'reasoning_content'):
                        reasoning_chunk = delta.reasoning_content
                    elif isinstance(delta, dict) and 'reasoning_content' in delta:
                        reasoning_chunk = delta['reasoning_content']
                
                # Handle reasoning tags
                if reasoning_chunk:
                    reasoning_content += reasoning_chunk
                    if not has_started_reasoning:
                        yield "<think>\n"
                        has_started_reasoning = True
                    yield reasoning_chunk
                
                # Extract content
                if hasattr(response, 'content') and response.content:
                    content_chunk = response.content
                elif hasattr(response, 'delta') and response.delta:
                    content_chunk = response.delta
                elif isinstance(response, str):
                    content_chunk = response
                
                # Agno's RunResponse might wrap content differently
                if not content_chunk and hasattr(response, 'response_delta') and response.response_delta:
                     delta = response.response_delta
                     if isinstance(delta, str):
                         content_chunk = delta
                     elif hasattr(delta, 'content'):
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
            
            # 5. Save Assistant Message to DB (Background or here)
            # We need a new DB session because the outer one might be closed or busy?
            # Actually we can use the `db` dependency but we need to be careful with async generators.
            # Best practice: use a separate session or do it after yield loop (but yield loop returns).
            # We will use a separate async function to save.
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
            await save_assistant_message(session_id, full_response, None if not meta.get("reasoning") else meta["reasoning"])
            if meta:
                await save_message_meta(session_id, meta)
            
        except Exception as e:
            msg = str(e)
            if "Missing reasoning_content field" in msg:
                logger.error("DeepSeek Thinking Mode error: assistant message缺少reasoning_content。已在历史构造阶段进行自动补全，请检查本次对话内的工具调用环节是否正确回传reasoning_content。")
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
            msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=content,
                meta_data={"reasoning": reasoning} if reasoning else None
            )
            db.add(msg)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to save assistant message: {e}")

async def save_message_meta(session_id: str, meta: dict):
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(desc(ChatMessage.created_at))
            )
            msg = result.scalars().first()
            if msg:
                base = msg.meta_data or {}
                for k, v in meta.items():
                    base[k] = v
                msg.meta_data = base
                db.add(msg)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update assistant message meta: {e}")
# Legacy endpoint (keep for compatibility if needed, or redirect)
@router.post("/completions")
async def chat_completions(request: ChatRequest):
    return StreamingResponse(qa_service.chat_stream(request.message), media_type="text/plain")
