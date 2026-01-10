from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
import logging
import json

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

from app.models.llm_model import LLMModel

@router.post("/sessions/{session_id}/chat")
async def chat_session(
    session_id: str,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Get Session
    result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Save User Message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    await db.commit()

    # 3. Get Agent
    agent = None
    if session.agent_id:
        try:
            agent = await agent_manager.create_agno_agent(db, session.agent_id, session_id)
        except Exception as e:
            logger.error(f"Failed to load agent {session.agent_id}: {e}")
            pass

    # If no agent or failed, use default qa_service (global agent)
    # Note: qa_service might need model update
    target_agent_runner = None
    
    if agent:
        # We need to load history into context manually if Agno agent is stateless here
        # Load history
        history_res = await db.execute(
            select(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        history_msgs = history_res.scalars().all()
        
        agno_history = []
        for msg in history_msgs:
            if msg.id == user_msg.id:
                continue
            
            # Construct message dict
            msg_dict = {"role": msg.role, "content": msg.content}
            
            # Check for reasoning_content in metadata (for DeepSeek Reasoner)
            if msg.role == "assistant" and msg.meta_data and "reasoning" in msg.meta_data:
                 # DeepSeek API expects 'reasoning_content' field if it was a thinking output
                 # Especially important if this assistant message was followed by a tool call (though here we just load history)
                 # But if we are continuing a conversation, it's safer to include it if the model supports it.
                 # Agno usually handles this if we pass it correctly.
                 msg_dict["reasoning_content"] = msg.meta_data["reasoning"]
            
            agno_history.append(msg_dict)
            
        target_agent_runner = lambda: agent.run(request.message, stream=True, messages=agno_history)
        
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

             return StreamingResponse(
                 iter([error_msg]), 
                 media_type="text/plain"
             )
        
        # If no agent_id, use qa_service but UPDATE it with a valid model first
        # Try to find a valid model to use for default chat
        from app.services.agent_manager import has_global_api_key
        
        # We need to find a model if:
        # 1. We want to support custom default models
        # 2. Global key is missing (fallback)
        
        active_model = None
        # Try to find ANY active model with a valid key
        res = await db.execute(
            select(LLMModel)
            .filter(LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
            .order_by(LLMModel.updated_at.desc())
        )
        active_model = res.scalars().first()
        
        if active_model:
            # Dynamically update the default QA service to use this model
            # Note: This changes the global singleton state, which might affect other concurrent requests 
            # using the default agent. Ideally QAAgentService should be instantiated per request or 
            # support passing model per run. 
            # Current `qa_service.chat_stream` supports `llm_model` arg which calls `_update_model`.
            # `_update_model` modifies `self.agent`. This IS a race condition risk but acceptable for single-user local app.
            target_agent_runner = lambda: qa_service.chat_stream(request.message, llm_model=active_model)
        else:
            # If no active model found, check if we have global key
            if has_global_api_key():
                 target_agent_runner = lambda: qa_service.chat_stream(request.message)
            else:
                 return StreamingResponse(
                     iter([f"Error: No active model found. Please configure a model in Settings or add OPENAI_API_KEY to .env."]), 
                     media_type="text/plain"
                 )

    # 4. Stream Response & Save Assistant Message
    async def event_generator():
        full_response = ""
        reasoning_content = ""
        
        try:
            stream = target_agent_runner()
            
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
            
            # 5. Save Assistant Message to DB (Background or here)
            # We need a new DB session because the outer one might be closed or busy?
            # Actually we can use the `db` dependency but we need to be careful with async generators.
            # Best practice: use a separate session or do it after yield loop (but yield loop returns).
            # We will use a separate async function to save.
            await save_assistant_message(session_id, full_response, reasoning_content)
            
        except Exception as e:
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

# Legacy endpoint (keep for compatibility if needed, or redirect)
@router.post("/completions")
async def chat_completions(request: ChatRequest):
    return StreamingResponse(qa_service.chat_stream(request.message), media_type="text/plain")
