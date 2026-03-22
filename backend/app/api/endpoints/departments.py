from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.crud.crud_user import department as crud_department
from app.api import deps
from app.schemas.user import Department, DepartmentCreate, DepartmentUpdate

router = APIRouter()

@router.get("/", response_model=List[Department])
async def read_departments(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve departments.
    """
    departments = await crud_department.get_multi_with_user_count(db, skip=skip, limit=limit)
    return departments

@router.post("/", response_model=Department)
async def create_department(
    *,
    db: AsyncSession = Depends(deps.get_db),
    department_in: DepartmentCreate,
) -> Any:
    """
    Create new department.
    """
    department = await crud_department.get_by_name(db, name=department_in.name)
    if department:
        raise HTTPException(
            status_code=400,
            detail="The department with this name already exists in the system.",
        )
    if department_in.code:
        department_by_code = await crud_department.get_by_code(db, code=department_in.code)
        if department_by_code:
            raise HTTPException(
                status_code=400,
                detail="The department with this code already exists in the system.",
            )
    department = await crud_department.create(db, obj_in=department_in)
    department.userCount = 0
    return department

@router.put("/{id}", response_model=Department)
async def update_department(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: str,
    department_in: DepartmentUpdate,
) -> Any:
    """
    Update a department.
    """
    department = await crud_department.get_with_user_count(db, id=id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    if department_in.name and department_in.name != department.name:
        department_by_name = await crud_department.get_by_name(db, name=department_in.name)
        if department_by_name:
            raise HTTPException(
                status_code=400,
                detail="The department with this name already exists in the system.",
            )
            
    if department_in.code and department_in.code != department.code:
        department_by_code = await crud_department.get_by_code(db, code=department_in.code)
        if department_by_code:
            raise HTTPException(
                status_code=400,
                detail="The department with this code already exists in the system.",
            )
            
    department = await crud_department.update(db, db_obj=department, obj_in=department_in)
    
    # re-fetch to get userCount
    department = await crud_department.get_with_user_count(db, id=id)
    return department

@router.get("/{id}", response_model=Department)
async def read_department(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: str,
) -> Any:
    """
    Get department by ID.
    """
    department = await crud_department.get_with_user_count(db, id=id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department

@router.delete("/{id}", response_model=Department)
async def delete_department(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: str,
) -> Any:
    """
    Delete a department.
    """
    department = await crud_department.get_with_user_count(db, id=id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    children = await crud_department.get_children(db, parent_id=id)
    if children:
        raise HTTPException(status_code=400, detail="Cannot delete department with child departments")
        
    if getattr(department, "userCount", 0) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete department with users")
        
    department = await crud_department.delete(db, id=id)
    department.userCount = 0
    return department
