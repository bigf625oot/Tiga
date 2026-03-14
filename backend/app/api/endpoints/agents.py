"""
Agent Endpoints
前端接口：
- POST /agents: 创建新的智能体
- GET /agents: 检索智能体列表
- GET /agents/{agent_id}: 获取单个智能体详情
- GET /agents/query: 查询智能体列表（支持根据名称、描述等查询）
- PUT /agents/{agent_id}: 更新智能体信息
- DELETE /agents/{agent_id}: 删除智能体
- POST /agents/{agent_id}/clone: 克隆智能体
- GET /agents/templates: 检索模板智能体列表
- GET /agents/active: 检索活动智能体列表


对应的前端页面：
- 智能体列表页（/agents）：展示所有智能体，支持创建、删除、更新智能体。
- 智能体详情页（/agents/{agent_id}）：展示智能体详情，支持更新智能体信息。
- 智能体查询页（/agents/query）：支持根据名称、描述等查询智能体。
- 智能体模板页（/agents/templates）：展示所有模板智能体，支持创建新智能体基于模板。
核心功能：
- 创建新的智能体
- 检索智能体列表（支持分页、查询、模板、活动状态过滤）
- 获取单个智能体详情
- 更新智能体信息
- 删除智能体
- 克隆智能体
"""
from typing import List
import shutil
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.i18n import _
from app.crud.crud_agent import agent as crud_agent
from app.db.session import get_db
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate, AgentClone

router = APIRouter()


@router.post("/upload/icon", summary=_("Upload agent icon"), description=_("Upload an icon for the agent."))
async def upload_agent_icon(file: UploadFile = File(...)):
    """
    Upload agent icon.
    """
    # Ensure directory exists
    # Assuming backend root is d:\Tiga\backend
    # We want to save to d:\Tiga\backend\data\storage\icons
    # But better to use relative path if possible or config.
    # For now, let's hardcode relative to current file or project root if possible.
    # But environment says working directory is d:\Tiga.
    
    upload_dir = Path("d:/Tiga/backend/data/storage/icons")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = upload_dir / filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/uploads/icons/{filename}"}


@router.get("/", response_model=List[AgentResponse], summary=_("Retrieve agents"), description=_("Retrieve a list of agents with pagination and filtering."))
async def read_agents(
    db: AsyncSession = Depends(get_db), 
    skip: int = 0, 
    limit: int = 100,
    q: str = None,
    is_template: bool = None,
    is_active: bool = None
):
    """
    Retrieve agents.
    """
    from app.services.eah_agent.core.service import agent_service
    agents = await agent_service.get_agents(db, skip=skip, limit=limit, query=q, is_template=is_template, is_active=is_active)
    return agents


@router.post("/", response_model=AgentResponse, summary=_("Create agent"), description=_("Create a new agent."))
async def create_agent(*, db: AsyncSession = Depends(get_db), agent_in: AgentCreate):
    """
    Create new agent.
    """
    from app.services.eah_agent.core.service import agent_service
    agent = await agent_service.create_agent(db, agent_in)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse, summary=_("Get agent"), description=_("Get an agent by ID."))
async def read_agent(*, db: AsyncSession = Depends(get_db), agent_id: str):
    """
    Get agent by ID.
    """
    from app.services.eah_agent.core.service import agent_service
    agent = await agent_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=_("Agent not found"))
    return agent


@router.put("/{agent_id}", response_model=AgentResponse, summary=_("Update agent"), description=_("Update an existing agent."))
async def update_agent(*, db: AsyncSession = Depends(get_db), agent_id: str, agent_in: AgentUpdate):
    """
    Update an agent.
    """
    from app.services.eah_agent.core.service import agent_service
    agent = await agent_service.update_agent(db, agent_id, agent_in)
    if not agent:
        raise HTTPException(status_code=404, detail=_("Agent not found"))
    return agent


@router.post("/{agent_id}/clone", response_model=AgentResponse, summary=_("Clone agent"), description=_("Clone an existing agent."))
async def clone_agent(*, db: AsyncSession = Depends(get_db), agent_id: str, clone_in: AgentClone):
    """
    Clone an agent.
    """
    from app.services.eah_agent.core.service import agent_service
    agent = await agent_service.clone_agent(db, agent_id, clone_in)
    if not agent:
        raise HTTPException(status_code=404, detail=_("Agent not found"))
    return agent


@router.delete("/batch", summary=_("Batch delete agents"), description=_("Delete multiple agents by ID."))
async def delete_agents_batch(*, db: AsyncSession = Depends(get_db), agent_ids: List[str] = Body(..., embed=True)):
    """
    Batch delete agents.
    """
    from app.services.eah_agent.core.service import agent_service
    deleted_ids = await agent_service.delete_agents(db, agent_ids)
    return {"deleted": deleted_ids}


@router.delete("/{agent_id}", response_model=AgentResponse, summary=_("Delete agent"), description=_("Delete an agent by ID."))
async def delete_agent(*, db: AsyncSession = Depends(get_db), agent_id: str):
    """
    Delete an agent.
    """
    from app.services.eah_agent.core.service import agent_service
    agent = await agent_service.delete_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=_("Agent not found"))
    return agent
