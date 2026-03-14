"""
Chat Endpoints（/chat）
前端接口：
- POST /chat/sessions: 创建新会话
- POST /chat/sessions/{session_id}: 发送消息到会话
- GET /chat/sessions/{session_id}: 获取会话详情
- PUT /chat/sessions/{session_id}: 更新会话状态
- DELETE /chat/sessions/{session_id}: 删除会话
对应的前端页面：
- 聊天首页（/chat）：展示会话列表页和会话详情页的切换。
- 会话列表页（/chat/sessions）：展示所有会话，支持创建、删除、更新会话。
- 会话详情页（/chat/sessions/{session_id}）：展示会话历史记录，支持发送消息、更新会话状态。
支持的模式：
- Chat: 基础的文本聊天模式。
- Task: 执行具体任务（如数据处理、API调用）。
- Team: 多智能体合作模式（如代码审查、团队合作）。
- Workflow: 复杂的工作流模式（如数据清洗、ETL流程）。
- Data Query: 数据库查询模式。
- KG QA: 知识图谱问答模式。
前端文件：
- `app/frontend/src/pages/Chat.vue`
功能模块：
- 聊天会话管理
- 消息发送和接收
- 会话状态更新
- 会话删除
"""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_chat import chat as crud_chat
from app.db.session import get_db
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate
from app.services.eah_agent.core.qa import qa_service  # Fallback

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
    """
    统一聊天端点，根据意图路由到适当的处理程序。
    支持: Chat, Task, Team, Workflow, Data Query, KG QA.
    """
    # New Control Plane
    from app.services.eah_agent.core.control_plane import AgnoControlPlane
    
    # Get active model for ControlPlane
    # In a real scenario, we might resolve this better or pass None to let ControlPlane resolve default
    control_plane = AgnoControlPlane()
    
    # Use SSE
    async def sse_generator():
        async for chunk in control_plane.process_stream(
            user_input=request.message, 
            db=db, 
            session_id=session_id
        ):
            # Format SSE
            event_type = chunk.get("type", "message")
            data = chunk.get("content", "")
            
            # Map internal types to frontend expected types if needed
            if event_type == "content":
                yield f"event: text\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            elif event_type == "think":
                yield f"event: think\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            elif event_type == "chart":
                # Frontend expects 'chart' event with config
                yield f"event: chart\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            elif event_type == "status":
                # Frontend might expect 'meta' or specific status events
                # For now, let's send as 'status' event
                yield f"event: status\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            elif event_type == "error":
                yield f"event: error\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            else:
                # Default fallback
                yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


# Legacy endpoint (keep for compatibility if needed, or redirect)
@router.post("/completions")
async def chat_completions(request: ChatRequest):
    return StreamingResponse(qa_service.chat_stream(request.message), media_type="text/plain")
