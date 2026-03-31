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
import uuid
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.agent import agent as crud_agent
from app.crud.chat import chat as crud_chat
from app.db.session import get_db
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate
from app.core.sse import format_sse_json
from app.services.domain.media.chat_attachments import ingest_chat_file, normalize_doc_ids
from app.services.agent.utils.title_generator import TitleGenerator
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


@router.delete("/sessions/{session_id}/messages/{message_id}")
async def delete_message(session_id: str, message_id: int, db: AsyncSession = Depends(get_db)):
    await crud_chat.delete_message(db, session_id, message_id)
    return {"status": "deleted"}


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
    parent_id: Optional[int] = None # 兼容 frontend 传来的 parent_id
    parent_message_id: Optional[int] = None # 用于 Regenerate 构建对话分支树


@router.post("/sessions/{session_id}/chat")
async def chat_session(
    session_id: str, 
    request: ChatRequest, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    """
    统一聊天端点，根据意图路由到适当的处理程序。
    支持: Chat, Task, Team, Workflow, Data Query, KG QA.
    """
    # New Control Plane
    from app.services.agent.orchestration.control_plane import AgnoControlPlane
    from app.services.platform.llm.resolver import resolve_chat_llm_model
    
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
    
    # 判断是否走 NexusExecutor 路径（规划型任务模式）
    _PLANNING_MODES = {"task", "solo", "team", "workflow"}
    is_planning_mode = effective_mode in _PLANNING_MODES

    # Use SSE
    async def sse_generator():
        # --- TEST INTERCEPTOR FOR SYSTEMATIC DEBUGGING ---
        if request.message.startswith("[TEST]"):
            user_msg = await crud_chat.create_message(
                db, 
                session_id=session_id, 
                role="user", 
                content=request.message,
                parent_id=request.parent_message_id
            )
            test_type = request.message.split(" ")[1] if " " in request.message else ""
            
            if test_type == "EMPTY_THOUGHT":
                # 场景：空 Thought 返回
                yield format_sse_json("think", "")
                yield format_sse_json("text", "这是没有思考过程的直接回复。")
                yield format_sse_json("done", "[DONE]")
                return
                
            elif test_type == "OUT_OF_ORDER":
                # 场景：SSE 消息乱序
                yield format_sse_json("text", "这是第一段正文。")
                yield format_sse_json("call", {"tool": "search", "args": {"query": "test"}})
                yield format_sse_json("text", "这是第二段正文。")
                yield format_sse_json("result", {"tool": "search", "output": "搜索结果"})
                yield format_sse_json("done", "[DONE]")
                return
                
            elif test_type == "JSON_ESCAPE":
                # 场景：JSON 转义字符攻击
                # 包含极多 \n 和 " 等
                malicious = "破坏性测试: \n \"\"\" {\"k\": \"v\\n\"} \r\n"
                yield format_sse_json("text", malicious)
                yield format_sse_json("done", "[DONE]")
                return

            elif test_type == "LONG_PLAN":
                # 场景：Plan 描述过长
                long_desc = "这是一个非常非常长的计划步骤描述，" * 10
                yield format_sse_json("step", {"id": 1, "content": long_desc})
                yield format_sse_json("text", "计划已生成。")
                yield format_sse_json("done", "[DONE]")
                return

            elif test_type == "TOOL_ERROR":
                # 场景：工具执行失败
                yield format_sse_json("call", {"tool": "python", "args": {"code": "print(1/0)"}})
                yield format_sse_json("result", {"tool": "python", "is_error": True, "output": "ZeroDivisionError: division by zero"})
                yield format_sse_json("text", "执行失败。")
                yield format_sse_json("done", "[DONE]")
                return
                
            elif test_type == "RECURSIVE_THINK":
                # 场景：递归思考
                yield format_sse_json("think", "第一步：分析问题\n")
                yield format_sse_json("think", "第二步：嵌套推导 -> a^2 + b^2 = c^2\n")
                yield format_sse_json("text", "分析完毕。")
                yield format_sse_json("done", "[DONE]")
                return

            # Default fallback for unhandled test types
            yield format_sse_json("text", f"Test {test_type} executed.")
            yield format_sse_json("done", "[DONE]")
            return
        # --- END TEST INTERCEPTOR ---

        # ── AgnoControlPlane 路径：支持所有模式 ──
        req_parent_id = request.parent_id or request.parent_message_id
        
        # 幂等性/防抖处理：如果最近的一条用户消息内容与 parent_id 完全一致，则复用该消息（防止网络重试导致生成孤儿节点）
        history = await crud_chat.get_history(db, session_id)
        duplicate_msg = None
        if history:
            last_msg = history[-1]
            if last_msg.role == "user" and last_msg.content == request.message and last_msg.parent_id == req_parent_id:
                duplicate_msg = last_msg
                
        if duplicate_msg:
            user_msg = duplicate_msg
        else:
            user_msg = await crud_chat.create_message(
                db, 
                session_id=session_id, 
                role="user", 
                content=request.message,
                parent_id=req_parent_id
            )

        text_parts: List[str] = []
        think_parts: List[str] = []
        cp_stream_events: List[Dict[str, Any]] = []

        async for chunk in control_plane.process_stream(
            user_input=request.message,
            db=db,
            session_id=session_id,
            user_id=session.user_id if session and session.user_id else "default_user",
            agent_id=effective_agent_id,
            mode=effective_mode,
            intent_override=request.intent,
            persist_user_message=False,
            persist_assistant_message=False,
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
            event_type = chunk.get("type", "message")
            
            # 强行拦截并格式化，避免嵌套 JSON 字符串直接流出
            if isinstance(chunk.get("content"), dict) and event_type in ("content", "text_delta"):
                logger.warning(f"Unexpected dict in content frame: {chunk}")
                inner_chunk = chunk["content"]
                event_type = inner_chunk.get("type", "message")
                chunk = inner_chunk

            if event_type == "content" or event_type == "text_delta":
                sse_event = "text"
                chunk_data = chunk.get("content", "")
                if isinstance(chunk_data, str) and chunk_data.strip().startswith('{"type":') and '"status":' in chunk_data:
                     try:
                         parsed = __import__("json").loads(chunk_data)
                         if parsed.get("type") == "text_delta":
                             chunk_data = parsed.get("content", "")
                         else:
                             continue
                     except Exception:
                         pass
                text_parts.append(chunk_data)
            elif event_type == "think":
                sse_event = "think"
                chunk_data = chunk.get("content", "")
                think_parts.append(chunk_data)
            elif event_type == "chart":
                sse_event = "chart"
                chunk_data = chunk
            elif event_type == "status":
                sse_event = "status"
                chunk_data = chunk.get("content", chunk)
            elif event_type == "error":
                sse_event = "error"
                chunk_data = chunk
            else:
                sse_event = event_type
                chunk_data = chunk

            cp_stream_events.append({
                "event": sse_event,
                "content": chunk_data,
                "raw": chunk
            })
            yield format_sse_json(sse_event, chunk_data)

        # 提取 tools 状态用于物化视图
        materialized_tools = []
        if cp_stream_events:
            for ev in cp_stream_events:
                event_type = ev.get("event")
                raw_content = ev.get("content")
                if event_type in ("tool_call", "call", "tool_start"):
                    info = raw_content
                    if isinstance(info, str):
                        import json
                        try:
                            info = json.loads(info)
                        except Exception:
                            info = {"tool": info}
                    elif not isinstance(info, dict):
                        info = {"tool": str(info)}
                    
                    payload = info.get("content") if isinstance(info.get("content"), dict) else info
                    
                    tool_id = payload.get("tool_call_id") or payload.get("id") or str(uuid.uuid4())
                    tool_name = payload.get("tool") or payload.get("name") or "unknown_tool"
                    args = payload.get("args") or payload.get("arguments") or {}
                    materialized_tools.append({
                        "id": tool_id,
                        "name": tool_name,
                        "args": args,
                        "status": "running"
                    })
                elif event_type in ("tool_output", "result", "tool_end", "tool_error"):
                    info = raw_content
                    if isinstance(info, str):
                        import json
                        try:
                            info = json.loads(info)
                        except Exception:
                            info = {"tool": "unknown_tool", "output": info}
                    elif not isinstance(info, dict):
                        info = {"tool": "unknown_tool", "output": str(info)}
                    
                    payload = info.get("content") if isinstance(info.get("content"), dict) else info
                    
                    tool_name = payload.get("tool") or payload.get("name")
                    is_error = payload.get("is_error", False)
                    result_data = payload.get("result") or payload.get("output")
                    if not isinstance(result_data, str):
                        import json
                        result_data = json.dumps(result_data, ensure_ascii=False)
                    
                    # Find the last running tool with matching name
                    for t in reversed(materialized_tools):
                        if t["name"] == tool_name and t["status"] == "running":
                            t["status"] = "error" if is_error else "success"
                            t["result"] = result_data
                            break

        # 持久化助手消息
        await crud_chat.create_message(
            db,
            session_id=session_id,
            role="assistant",
            content="".join(text_parts),
            meta_data=None,  # 移除 stream_events，避免存储冗余数据导致数据膨胀
            tools=materialized_tools if materialized_tools else None,
            reasoning_content="".join(think_parts) or None,
            parent_id=user_msg.id
        )

        yield format_sse_json("done", "[DONE]")

        background_tasks.add_task(TitleGenerator.generate_title, session_id, db)

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@router.post("/sessions/{session_id}/chat_multipart")
async def chat_session_multipart(
    session_id: str,
    background_tasks: BackgroundTasks,
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
    parent_id: Optional[int] = Form(None),
    attachments: Optional[List[str]] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db),
):
    from app.services.agent.orchestration.control_plane import AgnoControlPlane
    from app.services.platform.llm.resolver import resolve_chat_llm_model

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

    user_msg_meta = {}
    if uploaded_files:
        user_msg_meta["files"] = uploaded_files

    # 幂等性/防抖处理：如果最近的一条用户消息内容与 parent_id 完全一致，则复用该消息
    history = await crud_chat.get_history(db, session_id)
    duplicate_msg = None
    if history:
        last_msg = history[-1]
        if last_msg.role == "user" and last_msg.content == message and last_msg.parent_id == parent_id:
            # 简单对比，如果有文件就不复用了，为了安全起见
            if not uploaded_files:
                duplicate_msg = last_msg

    if duplicate_msg:
        user_msg = duplicate_msg
    else:
        user_msg = await crud_chat.create_message(
            db,
            session_id=session_id,
            role="user",
            content=message,
            parent_id=parent_id,
            meta_data=user_msg_meta if user_msg_meta else None
        )

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

        text_parts: List[str] = []
        think_parts: List[str] = []
        cp_stream_events: List[Dict[str, Any]] = []

        async for chunk in control_plane.process_stream(
            user_input=message,
            db=db,
            session_id=session_id,
            user_id=session.user_id if session and session.user_id else "default_user",
            agent_id=effective_agent_id,
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
            persist_user_message=False,
            persist_assistant_message=False,
        ):
            # 映射内部事件类型到前端期望的 SSE 事件类型
            event_type = chunk.get("type", "message")
            
            # 强行拦截并格式化，避免嵌套 JSON 字符串直接流出
            if isinstance(chunk.get("content"), dict) and event_type in ("content", "text_delta"):
                # 如果底层意外地将控制对象当做了 content 吐出，在这里解包
                logger.warning(f"Unexpected dict in content frame: {chunk}")
                inner_chunk = chunk["content"]
                event_type = inner_chunk.get("type", "message")
                chunk = inner_chunk
                
            if event_type == "content" or event_type == "text_delta":
                sse_event = "text"
                chunk_data = chunk.get("content", "")
                if isinstance(chunk_data, str) and chunk_data.strip().startswith('{"type":') and '"status":' in chunk_data:
                     # Fallback in case a raw JSON string made its way here
                     try:
                         parsed = __import__("json").loads(chunk_data)
                         if parsed.get("type") == "text_delta":
                             chunk_data = parsed.get("content", "")
                         else:
                             # It's another type of control frame hiding in text
                             continue
                     except Exception:
                         pass
                text_parts.append(chunk_data)
            elif event_type == "think":
                sse_event = "think"
                chunk_data = chunk.get("content", "")
                think_parts.append(chunk_data)
            elif event_type == "chart":
                sse_event = "chart"
                chunk_data = chunk
            elif event_type == "status":
                sse_event = "status"
                chunk_data = chunk.get("content", chunk)
            elif event_type == "error":
                sse_event = "error"
                chunk_data = chunk
            else:
                sse_event = event_type
                chunk_data = chunk

            cp_stream_events.append({
                "event": sse_event,
                "content": chunk_data,
                "raw": chunk
            })
            yield format_sse_json(sse_event, chunk_data)

        # 提取 tools 状态用于物化视图
        materialized_tools = []
        if cp_stream_events:
            for ev in cp_stream_events:
                event_type = ev.get("event")
                raw_content = ev.get("content")
                if event_type in ("tool_call", "call", "tool_start"):
                    info = raw_content
                    if isinstance(info, str):
                        import json
                        try:
                            info = json.loads(info)
                        except Exception:
                            info = {"tool": info}
                    elif not isinstance(info, dict):
                        info = {"tool": str(info)}
                    
                    payload = info.get("content") if isinstance(info.get("content"), dict) else info
                    
                    tool_id = payload.get("tool_call_id") or payload.get("id") or str(uuid.uuid4())
                    tool_name = payload.get("tool") or payload.get("name") or "unknown_tool"
                    args = payload.get("args") or payload.get("arguments") or {}
                    materialized_tools.append({
                        "id": tool_id,
                        "name": tool_name,
                        "args": args,
                        "status": "running"
                    })
                elif event_type in ("tool_output", "result", "tool_end", "tool_error"):
                    info = raw_content
                    if isinstance(info, str):
                        import json
                        try:
                            info = json.loads(info)
                        except Exception:
                            info = {"tool": "unknown_tool", "output": info}
                    elif not isinstance(info, dict):
                        info = {"tool": "unknown_tool", "output": str(info)}
                    
                    payload = info.get("content") if isinstance(info.get("content"), dict) else info
                    
                    tool_name = payload.get("tool") or payload.get("name")
                    is_error = payload.get("is_error", False)
                    result_data = payload.get("result") or payload.get("output")
                    if not isinstance(result_data, str):
                        import json
                        result_data = json.dumps(result_data, ensure_ascii=False)
                    
                    # Find the last running tool with matching name
                    for t in reversed(materialized_tools):
                        if t["name"] == tool_name and t["status"] == "running":
                            t["status"] = "error" if is_error else "success"
                            t["result"] = result_data
                            break

        # 持久化助手消息
        await crud_chat.create_message(
            db,
            session_id=session_id,
            role="assistant",
            content="".join(text_parts),
            meta_data=None,  # 移除 stream_events，避免存储冗余数据导致数据膨胀
            tools=materialized_tools if materialized_tools else None,
            reasoning_content="".join(think_parts) or None,
            parent_id=user_msg.id
        )

        yield format_sse_json("done", "[DONE]")
        
        background_tasks.add_task(TitleGenerator.generate_title, session_id, db)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.get("/sessions/{session_id}/stream")
async def resume_stream(
    session_id: str,
    agent_run_id: str = Query(..., description="NexusExecutor 运行 ID，由 /chat 的 meta 事件返回"),
    resume_from: str = Query("0-0", description="Redis Stream ID，从此位置之后回放"),
    db: AsyncSession = Depends(get_db),
):
    """
    断线续传端点：从 Redis Stream 回放历史 AgentEvent。
    前端断线后携带 agent_run_id 和最后一条事件的 Redis ID 调用此接口，
    服务端从 Redis Stream 中重放该位置之后的所有事件。
    """
    from app.services.agent.orchestration.control_plane import AgnoControlPlane
    
    control_plane = AgnoControlPlane()

    async def sse_gen():
        # TODO: Handle replay from control plane if needed
        # Fallback to just sending done for now
        yield format_sse_json("done", "[DONE]")

    return StreamingResponse(
        sse_gen(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
