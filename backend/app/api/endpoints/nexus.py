"""
Nexus Run Endpoint
──────────────────
POST /nexus/run          — 启动新的 Agent 任务，返回 agent_run_id
GET  /nexus/run/{run_id} — SSE 流，实时推送 AgentEvent（支持断线续传）
"""
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.eah_agent.core.nexus_executor import NexusExecutor

router = APIRouter()
logger = logging.getLogger("eah.api.nexus")


class NexusRunRequest(BaseModel):
    session_id: str
    user_goal: str
    images: Optional[list[str]] = None


class NexusRunResponse(BaseModel):
    agent_run_id: str


@router.post("/run", response_model=NexusRunResponse)
async def create_run(payload: NexusRunRequest):
    """
    分配 agent_run_id 并立即返回。
    前端随后建立 GET /nexus/run/{agent_run_id} 的 SSE 连接。
    run_id 同时作为 Redis Stream key 的后缀，支持断线续传。
    """
    run_id = str(uuid.uuid4())
    return NexusRunResponse(agent_run_id=run_id)


@router.get("/run/{agent_run_id}")
async def stream_run(
    agent_run_id: str,
    session_id: str = Query(...),
    user_goal: str = Query(...),
    resume_from: Optional[str] = Query(default=None, description="Redis Stream ID，断线续传起点"),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE 端点：建立连接后实时接收 AgentEvent。

    协议：
      Content-Type: text/event-stream
      每条事件格式：`data: <AgentEvent JSON>\\n\\n`
      流结束：`data: [DONE]\\n\\n`

    断线续传：
      重连时传入 resume_from=<上次收到的 Redis Stream ID>，
      服务端从 Redis 回放历史事件，然后继续执行（若任务仍在运行）。
    """
    executor = NexusExecutor(
        agent_run_id=agent_run_id,
        session_id=session_id,
        db=db,
        user_goal=user_goal,
        resume_from=resume_from,
    )

    async def event_generator():
        try:
            async for event in executor.stream():
                yield event.sse_encode()
        except Exception as exc:
            logger.exception(f"[NexusSSE] run={agent_run_id} error: {exc}")
            yield f'data: {{"type":"error","content":"{exc}","agent_run_id":"{agent_run_id}"}}\n\n'
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # 禁用 Nginx 缓冲
            "Connection": "keep-alive",
        },
    )
