from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate
from app.core.security import encrypt_password

class CRUDDataSource:
    async def get(self, db: AsyncSession, id: int):
        result = await db.execute(select(DataSource).filter(DataSource.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(DataSource).offset(skip).limit(limit).order_by(DataSource.created_at.desc()))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: DataSourceCreate):
        obj_data = obj_in.model_dump(exclude={'password'})
        
        # Encrypt password if provided
        if obj_in.password:
            obj_data['password_encrypted'] = encrypt_password(obj_in.password)
            
        db_obj = DataSource(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: DataSource, obj_in: DataSourceUpdate):
        update_data = obj_in.model_dump(exclude_unset=True, exclude={'password'})
        
        if obj_in.password:
            update_data['password_encrypted'] = encrypt_password(obj_in.password)
            
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int):
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

data_source = CRUDDataSource()
