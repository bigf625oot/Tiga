import json
import inspect
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
    await crud_chat.remove(db, session_id)
    # Idempotent: Always return success even if not found
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
    enable_search: bool = True


@router.post("/sessions/{session_id}/chat")
async def chat_session(session_id: str, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    from app.services.chat.service import chat_service
    
    return StreamingResponse(
        chat_service.process_chat(
            session_id=session_id,
            message=request.message,
            db=db,
            enable_search=request.enable_search,
            strict_mode=request.strict_mode,
            threshold=request.threshold,
            debug=request.debug,
            ab_variant=request.ab_variant,
            attachments=request.attachments
        ),
        media_type="text/plain"
    )


# Legacy endpoint (keep for compatibility if needed, or redirect)
@router.post("/completions")
async def chat_completions(request: ChatRequest):
    return StreamingResponse(qa_service.chat_stream(request.message), media_type="text/plain")
