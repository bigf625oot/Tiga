from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Header, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.sql import func
import jwt

from app.db.session import AsyncSessionLocal
from app.models.user_tool import UserTool

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = authorization.replace("Bearer ", "")
        # Unverified decode for demonstration as no SECRET is available in context
        # In production, use secret key: jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        if not user_id:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_current_user_tools(
    tool_id: str = Path(..., description="The ID of the tool"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> UserTool:
    """
    Dependency to verify if the current user has access to the tool.
    Returns the UserTool association if access is granted, raises 403 otherwise.
    """
    stmt = select(UserTool).where(
        UserTool.user_id == user_id,
        UserTool.tool_id == tool_id,
        or_(UserTool.expires_at == None, UserTool.expires_at > func.now())
    )
    result = await db.execute(stmt)
    user_tool = result.scalars().first()

    if not user_tool:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tool"
        )
    return user_tool
