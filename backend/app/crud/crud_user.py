from typing import List, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json

from app.models.user import User, Role, Department
from app.schemas.user import UserCreate, UserUpdate, RoleCreate, RoleUpdate, DepartmentCreate, DepartmentUpdate
from app.core.security import encrypt_password

class CRUDRole:
    async def get(self, db: AsyncSession, id: str) -> Optional[Role]:
        result = await db.execute(select(Role).filter(Role.id == id))
        return result.scalars().first()

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Role]:
        result = await db.execute(select(Role).filter(Role.code == code))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Role]:
        result = await db.execute(select(Role).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_multi_with_user_count(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Role]:
        roles = await self.get_multi(db, skip, limit)
        for role in roles:
            count_result = await db.execute(select(func.count(User.id)).where(User.role_id == role.id))
            role.userCount = count_result.scalar() or 0
        return roles

    async def create(self, db: AsyncSession, obj_in: RoleCreate) -> Role:
        obj_data = obj_in.model_dump()
        if 'permissions' in obj_data and isinstance(obj_data['permissions'], list):
            obj_data['permissions'] = json.dumps(obj_data['permissions'])
        db_obj = Role(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: Role, obj_in: RoleUpdate) -> Role:
        update_data = obj_in.model_dump(exclude_unset=True)
        if 'permissions' in update_data and isinstance(update_data['permissions'], list):
            update_data['permissions'] = json.dumps(update_data['permissions'])
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: str) -> Optional[Role]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

class CRUDDepartment:
    async def get(self, db: AsyncSession, id: str) -> Optional[Department]:
        result = await db.execute(select(Department).filter(Department.id == id))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Department]:
        result = await db.execute(select(Department).filter(Department.name == name))
        return result.scalars().first()

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Department]:
        result = await db.execute(select(Department).filter(Department.code == code))
        return result.scalars().first()

    async def get_children(self, db: AsyncSession, parent_id: str) -> List[Department]:
        result = await db.execute(select(Department).filter(Department.parent_id == parent_id))
        return list(result.scalars().all())

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Department]:
        result = await db.execute(select(Department).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_with_user_count(self, db: AsyncSession, id: str) -> Optional[Department]:
        dept = await self.get(db, id)
        if dept:
            count_result = await db.execute(select(func.count(User.id)).where(User.department_id == id))
            dept.userCount = count_result.scalar() or 0
        return dept

    async def get_multi_with_user_count(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Department]:
        depts = await self.get_multi(db, skip, limit)
        for dept in depts:
            count_result = await db.execute(select(func.count(User.id)).where(User.department_id == dept.id))
            dept.userCount = count_result.scalar() or 0
        return depts

    async def create(self, db: AsyncSession, obj_in: DepartmentCreate) -> Department:
        obj_data = obj_in.model_dump()
        db_obj = Department(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: Department, obj_in: DepartmentUpdate) -> Department:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: str) -> Optional[Department]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

class CRUDUser:
    async def get(self, db: AsyncSession, id: str) -> Optional[User]:
        result = await db.execute(
            select(User)
            .options(selectinload(User.role), selectinload(User.department))
            .filter(User.id == id)
        )
        return result.scalars().first()
        
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, 
        query: Optional[str] = None, status: Optional[bool] = None, role_id: Optional[str] = None
    ) -> List[User]:
        stmt = select(User).options(selectinload(User.role), selectinload(User.department))
        
        if status is not None:
            stmt = stmt.filter(User.status == status)
            
        if role_id is not None:
            stmt = stmt.filter(User.role_id == role_id)
            
        if query:
            search = f"%{query}%"
            stmt = stmt.filter(or_(
                User.username.ilike(search),
                User.email.ilike(search),
                User.phone.ilike(search)
            ))
            
        stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()
        
    async def get_count(
        self, db: AsyncSession, query: Optional[str] = None, 
        status: Optional[bool] = None, role_id: Optional[str] = None
    ) -> int:
        stmt = select(func.count(User.id))
        
        if status is not None:
            stmt = stmt.filter(User.status == status)
            
        if role_id is not None:
            stmt = stmt.filter(User.role_id == role_id)
            
        if query:
            search = f"%{query}%"
            stmt = stmt.filter(or_(
                User.username.ilike(search),
                User.email.ilike(search),
                User.phone.ilike(search)
            ))
            
        result = await db.execute(stmt)
        return result.scalar_one()

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        obj_data = obj_in.model_dump(exclude={"password"})
        obj_data["hashed_password"] = encrypt_password(obj_in.password)
        
        db_obj = User(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Load relationships
        return await self.get(db, db_obj.id)

    async def update(self, db: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = encrypt_password(update_data.pop("password"))
            
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return await self.get(db, db_obj.id)

    async def delete(self, db: AsyncSession, id: str) -> Optional[User]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

role = CRUDRole()
department = CRUDDepartment()
user = CRUDUser()
