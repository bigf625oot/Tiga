from typing import Any, Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.workflow.app_workflow import AppWorkflow
from app.crud.crud_chat import chat as crud_chat
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class WorkflowRunRequest(BaseModel):
    session_id: str
    message: str
    agent_id: Optional[str] = None
    mode: str = "static" # static or dynamic
    params: Dict[str, Any] = {}

@router.post("/run")
async def run_workflow(request: WorkflowRunRequest, db: AsyncSession = Depends(get_db)):
    """
    Execute workflow synchronously.
    """
    try:
        # Save User Message
        await crud_chat.create_message(db, request.session_id, "user", request.message)

        # Load history
        history_msgs = await crud_chat.get_history(db, request.session_id)
        history = [{"role": m.role, "content": m.content} for m in history_msgs]
        
        workflow = AppWorkflow(session_id=request.session_id, mode=request.mode)
        result = await workflow.run(
            user_message=request.message,
            agent_id=request.agent_id,
            history=history,
            **request.params
        )
        return {"status": "success", "output": result}
    except Exception as e:
        logger.error(f"Run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run_stream")
async def run_workflow_stream(request: WorkflowRunRequest, db: AsyncSession = Depends(get_db)):
    """
    Execute workflow with streaming SSE.
    """
    try:
        # Save User Message
        await crud_chat.create_message(db, request.session_id, "user", request.message)

        # Load history
        history_msgs = await crud_chat.get_history(db, request.session_id)
        history = [{"role": m.role, "content": m.content} for m in history_msgs]
        
        workflow = AppWorkflow(session_id=request.session_id, mode=request.mode)
        
        async def event_generator():
            async for event in workflow.run_stream(
                user_message=request.message,
                agent_id=request.agent_id,
                history=history,
                **request.params
            ):
                yield f"data: {event}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Stream init failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
