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
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_agent import agent as crud_agent
from app.crud.crud_chat import chat as crud_chat
from app.db.session import get_db
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate
from app.core.sse import format_sse_json
from app.services.media.chat_attachments import ingest_chat_file, normalize_doc_ids
from app.services.eah_agent.core.title_generator import TitleGenerator
from app.models.knowledge import KnowledgeDocument

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
    message: str  # 聊天消息内容
    stream: bool = True  # 是否启用流式响应
    mode: Optional[str] = None  # 聊天模式，可选值：chat, task, team, workflow, data_query, kg_qa
    intent: Optional[str] = None   # 意图分类，可选值：chat, task, team, workflow, data_query, kg_qa
    strict_mode: bool = False  # 是否严格遵循意图分类
    threshold: float = 0.85  # 意图分类阈值
    debug: bool = False  # 是否开启调试模式
    ab_variant: Optional[str] = None  # AB测试变体，可选值：control, variant_a, variant_b等
    attachments: Optional[List[str]] = None  # 附件ID列表，用于引用知识库文档
    enable_search: bool = True  # 是否启用知识库搜索
    enable_reasoning: bool = False  # 是否启用推理
    agent_id: Optional[str] = None  # 关联的智能体ID


@router.post("/sessions/{session_id}/chat")
async def chat_session(session_id: str, request: ChatRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    统一聊天端点，根据意图路由到适当的处理程序。
    支持: Chat, Task, Team, Workflow, Data Query, KG QA.
    """
    # New Control Plane
    from app.services.eah_agent.core.control_plane import AgnoControlPlane
    from app.services.llm.resolver import resolve_chat_llm_model
    
    # Get active model for ControlPlane
    # In a real scenario, we might resolve this better or pass None to let ControlPlane resolve default
    llm_model = await resolve_chat_llm_model(db)
    control_plane = AgnoControlPlane(llm_model=llm_model)

    session = await crud_chat.get(db, session_id)
    session_mode = getattr(session, "mode", None) if session else None
    effective_mode = request.mode or (session_mode if session_mode and session_mode != "chat" else None)
    doc_ids = normalize_doc_ids(request.attachments)
    agent_doc_ids: List[int] = []
    agent_strict_only = False
    
    # Priority: request.agent_id > session.agent_id
    effective_agent_id = request.agent_id or (session.agent_id if session else None)
    if effective_agent_id:
        agent = await crud_agent.get(db, effective_agent_id)
        if agent:
            knowledge_config: Dict[str, Any] = getattr(agent, "knowledge_config", None) or {}
            agent_doc_ids = normalize_doc_ids(knowledge_config.get("document_ids"))
            agent_strict_only = bool(knowledge_config.get("strict_only"))
            
    if agent_doc_ids:
        doc_ids = normalize_doc_ids([*doc_ids, *agent_doc_ids])
    effective_strict_mode = bool(request.strict_mode or agent_strict_only)
    kb_scope_context = None
    if doc_ids:
        try:
            rows = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id.in_(doc_ids))
            )
            docs = rows.scalars().all()
            if docs:
                kb_scope_context = "【本会话可用的知识库文档】\n" + "\n".join(
                    [
                        f"- doc#{d.id}:{d.filename} ({getattr(d.status, 'value', d.status)})"
                        for d in docs
                        if d and getattr(d, "id", None) is not None
                    ]
                )
        except Exception:
            kb_scope_context = None
    
    # Use SSE
    async def sse_generator():
        async for chunk in control_plane.process_stream(
            user_input=request.message, 
            db=db, 
            session_id=session_id,
            mode=effective_mode,
            intent_override=request.intent,
            doc_ids=doc_ids,
            enable_search=request.enable_search,
            enable_reasoning=request.enable_reasoning,
            strict_mode=effective_strict_mode,
            threshold=request.threshold,
            debug=request.debug,
            ab_variant=request.ab_variant,
            attachments=request.attachments,
            attachment_context=kb_scope_context,
        ):
            # Format SSE
            event_type = chunk.get("type", "message")
            data = chunk.get("content", "")
            
            # Map internal types to frontend expected types if needed
            if event_type == "content":
                yield format_sse_json("text", data)
            elif event_type == "think":
                yield format_sse_json("think", data)
            elif event_type == "chart":
                # Frontend expects 'chart' event with config
                yield format_sse_json("chart", data)
            elif event_type == "status":
                # Frontend might expect 'meta' or specific status events
                # For now, let's send as 'status' event
                yield format_sse_json("status", data)
            elif event_type == "error":
                yield format_sse_json("error", data)
            else:
                # Default fallback
                yield format_sse_json(event_type, data)
        
        yield format_sse_json("done", "[DONE]")
        
        background_tasks.add_task(TitleGenerator.generate_title, session_id, db)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.post("/sessions/{session_id}/chat_multipart")
async def chat_session_multipart(
    session_id: str,
    message: str = Form(...),
    stream: bool = Form(True),
    mode: Optional[str] = Form(None),
    intent: Optional[str] = Form(None),
    strict_mode: bool = Form(False),
    threshold: float = Form(0.85),
    debug: bool = Form(False),
    ab_variant: Optional[str] = Form(None),
    enable_search: bool = Form(True),
    enable_reasoning: bool = Form(False),
    agent_id: Optional[str] = Form(None),
    attachments: Optional[List[str]] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db),
):
    from app.services.eah_agent.core.control_plane import AgnoControlPlane
    from app.services.llm.resolver import resolve_chat_llm_model

    llm_model = await resolve_chat_llm_model(db)
    control_plane = AgnoControlPlane(llm_model=llm_model)

    session = await crud_chat.get(db, session_id)
    session_mode = getattr(session, "mode", None) if session else None
    effective_mode = mode or (session_mode if session_mode and session_mode != "chat" else None)

    doc_ids = normalize_doc_ids(attachments)
    agent_doc_ids: List[int] = []
    agent_strict_only = False
    
    # Priority: request.agent_id > session.agent_id
    effective_agent_id = agent_id or (session.agent_id if session else None)
    if effective_agent_id:
        agent = await crud_agent.get(db, effective_agent_id)
        if agent:
            knowledge_config: Dict[str, Any] = getattr(agent, "knowledge_config", None) or {}
            agent_doc_ids = normalize_doc_ids(knowledge_config.get("document_ids"))
            agent_strict_only = bool(knowledge_config.get("strict_only"))
            
    if agent_doc_ids:
        doc_ids = normalize_doc_ids([*doc_ids, *agent_doc_ids])
    effective_strict_mode = bool(strict_mode or agent_strict_only)
    kb_scope_context = None
    if doc_ids:
        try:
            rows = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id.in_(doc_ids))
            )
            docs = rows.scalars().all()
            if docs:
                kb_scope_context = "【本会话可用的知识库文档】\n" + "\n".join(
                    [
                        f"- doc#{d.id}:{d.filename} ({getattr(d.status, 'value', d.status)})"
                        for d in docs
                        if d and getattr(d, "id", None) is not None
                    ]
                )
        except Exception:
            kb_scope_context = None
    attachment_context_parts: List[str] = []
    uploaded_files: List[dict] = []
    if files:
        for f in files:
            meta = await ingest_chat_file(db, f)
            uploaded_files.append(meta)
            doc_id = meta.get("id")
            if isinstance(doc_id, int):
                doc_ids.append(doc_id)
            extracted = (meta.get("extracted_text") or "").strip()
            media_kind = meta.get("media_kind") or "file"
            if extracted:
                snippet = extracted
                if len(snippet) > 2000:
                    snippet = snippet[:2000]
                attachment_context_parts.append(f"[{media_kind}] doc#{doc_id}:{f.filename}\n{snippet}")

    attachment_context_parts_all = []
    if kb_scope_context:
        attachment_context_parts_all.append(kb_scope_context)
    if attachment_context_parts:
        attachment_context_parts_all.append("\n\n".join(attachment_context_parts))
    attachment_context = "\n\n".join(attachment_context_parts_all) if attachment_context_parts_all else None

    async def sse_generator():
        for meta in uploaded_files:
            status = (meta.get("status") or "").lower()
            ui_status = "parsing"
            if status == "indexed":
                ui_status = "success"
            elif status == "failed":
                ui_status = "error"
            payload = {
                "id": str(meta.get("id")),
                "title": meta.get("title") or meta.get("name"),
                "name": meta.get("name") or meta.get("title"),
                "size": meta.get("size"),
                "url": meta.get("oss_url"),
                "media_kind": meta.get("media_kind"),
                "status": ui_status,
                "errorMessage": meta.get("error_message"),
            }
            yield format_sse_json("file", payload)

        async for chunk in control_plane.process_stream(
            user_input=message,
            db=db,
            session_id=session_id,
            mode=effective_mode,
            intent_override=intent,
            doc_ids=doc_ids,
            attachment_context=attachment_context,
            enable_search=enable_search,
            strict_mode=effective_strict_mode,
            enable_reasoning=enable_reasoning,
            threshold=threshold,
            debug=debug,
            ab_variant=ab_variant,
            attachments=attachments,
        ):
            event_type = chunk.get("type", "message")
            data = chunk.get("content", "")

            if event_type == "content":
                yield format_sse_json("text", data)
            elif event_type == "think":
                yield format_sse_json("think", data)
            elif event_type == "chart":
                yield format_sse_json("chart", data)
            elif event_type == "status":
                yield format_sse_json("status", data)
            elif event_type == "error":
                yield format_sse_json("error", data)
            else:
                yield format_sse_json(event_type, data)

        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


