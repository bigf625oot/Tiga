from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from app.utils.crypto_utils import encrypt_field
from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate


class CRUDDataSource:
    async def get(self, db: AsyncSession, id: int) -> Optional[DataSource]:
        result = await db.execute(select(DataSource).filter(DataSource.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(DataSource).offset(skip).limit(limit).order_by(DataSource.created_at.desc()))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: DataSourceCreate) -> DataSource:
        exclude_fields = {"password", "api_key", "private_key", "token"}
        obj_data = obj_in.model_dump(exclude=exclude_fields)

        # Encrypt sensitive fields
        if obj_in.password:
            obj_data["password_encrypted"] = encrypt_field(obj_in.password)
        if obj_in.api_key:
            obj_data["encrypted_api_key"] = encrypt_field(obj_in.api_key)
        if obj_in.private_key:
            obj_data["encrypted_private_key"] = encrypt_field(obj_in.private_key)
        if obj_in.token:
            obj_data["encrypted_token"] = encrypt_field(obj_in.token)

        db_obj = DataSource(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: DataSource, obj_in: DataSourceUpdate) -> DataSource:
        exclude_fields = {"password", "api_key", "private_key", "token"}
        update_data = obj_in.model_dump(exclude_unset=True, exclude=exclude_fields)

        if obj_in.password:
            update_data["password_encrypted"] = encrypt_field(obj_in.password)
        if obj_in.api_key:
            update_data["encrypted_api_key"] = encrypt_field(obj_in.api_key)
        if obj_in.private_key:
            update_data["encrypted_private_key"] = encrypt_field(obj_in.private_key)
        if obj_in.token:
            update_data["encrypted_token"] = encrypt_field(obj_in.token)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> Optional[DataSource]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj


data_source = CRUDDataSource()
