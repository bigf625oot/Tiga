from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud.crud_team import team as crud_team
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate
from app.models.team import Team
from datetime import datetime

router = APIRouter()

# Hardcoded default teams
DEFAULT_TEAMS = [
    {
        "id": -1,
        "name": "研究团队",
        "description": "专业的综合研究团队。包含研究协调员、网络搜索员和作家。",
        "mode": "coordinate",
        "leader_id": "research_coordinator_agent",
        "members": ["search_agent", "writer_agent"], # Placeholder IDs, actual implementation uses specific agents
        "is_readonly": True,
        "created_at": datetime.min,
        "updated_at": datetime.min
    },
    {
        "id": -2,
        "name": "运维团队",
        "description": "执行运维任务（DevOps、数据录入等）的团队。包含运维经理、Shell执行器和文件管理器。",
        "mode": "coordinate",
        "leader_id": "operations_manager_agent",
        "members": ["shell_agent", "file_editor_agent"], # Placeholder IDs
        "is_readonly": True,
        "created_at": datetime.min,
        "updated_at": datetime.min
    }
]

@router.get("/", response_model=List[TeamResponse])
async def read_teams(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve teams (both default and user-created).
    """
    db_teams = await crud_team.get_multi(db, skip=skip, limit=limit)
    
    # Combine default teams and DB teams
    # Note: Default teams are always returned first
    all_teams = [TeamResponse(**t) for t in DEFAULT_TEAMS] + db_teams
    return all_teams

@router.post("/", response_model=TeamResponse)
async def create_team(
    *,
    db: AsyncSession = Depends(deps.get_db),
    team_in: TeamCreate,
) -> Any:
    """
    Create new team.
    """
    if team_in.is_readonly:
        raise HTTPException(status_code=400, detail="Cannot create read-only team")
    
    team_obj = await crud_team.create(db, obj_in=team_in)
    return team_obj

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    *,
    db: AsyncSession = Depends(deps.get_db),
    team_id: int,
    team_in: TeamUpdate,
) -> Any:
    """
    Update a team.
    """
    if team_id < 0:
        raise HTTPException(status_code=403, detail="Cannot update default teams")
        
    team_obj = await crud_team.get(db, id=team_id)
    if not team_obj:
        raise HTTPException(status_code=404, detail="Team not found")
        
    if team_obj.is_readonly:
        raise HTTPException(status_code=403, detail="Cannot update read-only team")
        
    team_obj = await crud_team.update(db, db_obj=team_obj, obj_in=team_in)
    return team_obj

@router.delete("/{team_id}", response_model=TeamResponse)
async def delete_team(
    *,
    db: AsyncSession = Depends(deps.get_db),
    team_id: int,
) -> Any:
    """
    Delete a team.
    """
    if team_id < 0:
        raise HTTPException(status_code=403, detail="Cannot delete default teams")
        
    team_obj = await crud_team.get(db, id=team_id)
    if not team_obj:
        raise HTTPException(status_code=404, detail="Team not found")
        
    if team_obj.is_readonly:
        raise HTTPException(status_code=403, detail="Cannot delete read-only team")
        
    team_obj = await crud_team.delete(db, id=team_id)
    return team_obj
