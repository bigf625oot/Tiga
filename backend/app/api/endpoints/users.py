import os
import uuid
import time
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional

from app.services.platform.storage.service import storage_service
from app.services.platform.notification.email import send_reset_password_email
from app.db.session import get_db
from app.crud.crud_user import user as crud_user, role as crud_role, department as crud_department
from app.schemas.user import User, UserCreate, UserUpdate, UserPage, Role, RoleCreate, RoleUpdate, Department

router = APIRouter()

@router.get("/roles", response_model=List[Role])
async def get_roles(db: AsyncSession = Depends(get_db)):
    """Get all roles with user count"""
    return await crud_role.get_multi_with_user_count(db=db, limit=100)

@router.post("/roles", response_model=Role)
async def create_role(
    *,
    db: AsyncSession = Depends(get_db),
    role_in: RoleCreate
):
    """Create new role"""
    existing = await crud_role.get_by_code(db=db, code=role_in.code)
    if existing:
        raise HTTPException(status_code=400, detail="Role code already exists")
    return await crud_role.create(db=db, obj_in=role_in)

@router.put("/roles/{role_id}", response_model=Role)
async def update_role(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: str,
    role_in: RoleUpdate
):
    """Update role"""
    role = await crud_role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system role")
    return await crud_role.update(db=db, db_obj=role, obj_in=role_in)

@router.delete("/roles/{role_id}")
async def delete_role(
    *,
    db: AsyncSession = Depends(get_db),
    role_id: str
):
    """Delete role"""
    role = await crud_role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    await crud_role.delete(db=db, id=role_id)
    return {"status": "success"}

@router.get("/departments", response_model=List[Department])
async def get_departments(db: AsyncSession = Depends(get_db)):
    """Get all departments"""
    return await crud_department.get_multi(db=db, limit=100)

@router.get("/", response_model=UserPage)
async def get_users(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    query: Optional[str] = None,
    status: Optional[str] = None,
    role_id: Optional[str] = None
):
    """Get users with pagination and filtering"""
    skip = (page - 1) * page_size
    
    status_bool = None
    if status == 'active':
        status_bool = True
    elif status == 'inactive':
        status_bool = False
        
    role_filter = None if role_id == 'all' or not role_id else role_id
    
    users = await crud_user.get_multi(
        db=db, skip=skip, limit=page_size, 
        query=query, status=status_bool, role_id=role_filter
    )
    total = await crud_user.get_count(
        db=db, query=query, status=status_bool, role_id=role_filter
    )
    
    return UserPage(items=users, total=total, page=page, page_size=page_size)

@router.post("/", response_model=User)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate
):
    """Create new user"""
    existing_user = await crud_user.get_by_username(db=db, username=user_in.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    return await crud_user.create(db=db, obj_in=user_in)

@router.put("/{user_id}", response_model=User)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: str,
    user_in: UserUpdate
):
    """Update user"""
    user = await crud_user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_in.username and user_in.username != user.username:
        existing_user = await crud_user.get_by_username(db=db, username=user_in.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
            
    return await crud_user.update(db=db, db_obj=user, obj_in=user_in)

@router.delete("/{user_id}")
async def delete_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: str
):
    """Delete user"""
    user = await crud_user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    await crud_user.delete(db=db, id=user_id)
    return {"status": "success"}

@router.post("/bulk-delete")
async def bulk_delete_users(
    *,
    db: AsyncSession = Depends(get_db),
    user_ids: List[str] = Body(..., embed=True)
):
    """Bulk delete users"""
    for uid in user_ids:
        await crud_user.delete(db=db, id=uid)
    return {"status": "success"}

@router.post("/bulk-status")
async def bulk_update_status(
    *,
    db: AsyncSession = Depends(get_db),
    user_ids: List[str] = Body(...),
    status: bool = Body(...)
):
    """Bulk update users status"""
    for uid in user_ids:
        user = await crud_user.get(db=db, id=uid)
        if user:
            await crud_user.update(db=db, db_obj=user, obj_in=UserUpdate(status=status))
    return {"status": "success"}

@router.post("/bulk-transfer-department")
async def bulk_transfer_department(
    *,
    db: AsyncSession = Depends(get_db),
    user_ids: List[str] = Body(...),
    department_id: Optional[str] = Body(None)
):
    """Bulk transfer users to a department"""
    for uid in user_ids:
        user = await crud_user.get(db=db, id=uid)
        if user:
            await crud_user.update(db=db, db_obj=user, obj_in=UserUpdate(department_id=department_id))
    return {"status": "success"}

@router.post("/{user_id}/reset-password")
async def reset_password(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: str
):
    """Reset user password and send notification email"""
    user = await crud_user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.email:
        raise HTTPException(status_code=400, detail="User has no email address configured")
        
    # Generate a random password
    new_password = "User@" + str(uuid.uuid4())[:8]
    
    # Try to send email first
    email_sent = await send_reset_password_email(user.email, new_password)
    
    if not email_sent:
        # In a production environment, you might want to fail the request if email sending fails.
        # Here we'll return a warning but still reset the password.
        pass
        
    # Update the database
    await crud_user.update(db=db, db_obj=user, obj_in=UserUpdate(password=new_password))
    
    return {
        "status": "success", 
        "new_password": new_password,
        "email_sent": email_sent,
        "message": "Password reset successfully. Email notification sent." if email_sent else "Password reset successfully, but failed to send email notification."
    }

@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload user avatar
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Generate a unique file name
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ".png"
    
    file_key = f"avatars/avatar_{uuid.uuid4().hex[:8]}_{int(time.time())}{ext}"
    
    try:
        # Read the file data
        data = await file.read()
        
        # Upload using storage service
        url = storage_service.upload_file_sync(file_key, data)
        
        # In a real scenario, we would save this URL to the database for the current user.
        # But since we just want to replace the frontend stub and there might not be user authentication setup,
        # returning the URL is enough for the frontend to display.
        
        return {
            "status": "success",
            "url": url,
            "message": "Avatar uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")
