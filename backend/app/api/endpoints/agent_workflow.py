from typing import Any, Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.eah_agent.core.executor import get_executor
from app.crud.crud_agent_workflow import agent_workflow as crud_agent_workflow
from app.crud import crud_chat
from app.schemas.agent_workflow import AgentWorkflowCreate, AgentWorkflowUpdate, AgentWorkflowResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[AgentWorkflowResponse])
async def read_workflows(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve agent workflows with optional search query.
    """
    workflows = await crud_agent_workflow.get_multi(db, skip=skip, limit=limit, query=q)
    return workflows

@router.post("/", response_model=AgentWorkflowResponse)
async def create_workflow(
    workflow_in: AgentWorkflowCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new agent workflow.
    """
    return await crud_agent_workflow.create(db, obj_in=workflow_in)

@router.get("/{workflow_id}", response_model=AgentWorkflowResponse)
async def read_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent workflow by ID.
    """
    workflow = await crud_agent_workflow.get(db, id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.put("/{workflow_id}", response_model=AgentWorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_in: AgentWorkflowUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update agent workflow.
    """
    workflow = await crud_agent_workflow.get(db, id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return await crud_agent_workflow.update(db, db_obj=workflow, obj_in=workflow_in)

@router.delete("/{workflow_id}", response_model=AgentWorkflowResponse)
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete agent workflow.
    """
    workflow = await crud_agent_workflow.get(db, id=workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await crud_agent_workflow.delete(db, id=workflow_id)
    return workflow

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
        
        executor = get_executor(request.mode, request.session_id)
        result = await executor.execute(
            message=request.message,
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
    执行工作流并返回流式 SSE 响应。
    返回完整的事件对象，包含 step, status, output, system 等字段，供前端渲染日志和进度。
    """
    try:
        # Save User Message
        await crud_chat.create_message(db, request.session_id, "user", request.message)

        # Load history
        history_msgs = await crud_chat.get_history(db, request.session_id)
        history = [{"role": m.role, "content": m.content} for m in history_msgs]
        
        executor = get_executor(request.mode, request.session_id)
        
        # 执行工作流并返回流式事件
        async def event_generator():
            async for event in executor.stream(
                message=request.message,
                agent_id=request.agent_id,
                history=history,
                **request.params
            ):
                if event is not None:
                    yield f"data: {event}\n\n"
            yield "data: [DONE]\n\n"
            
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Stream init failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
