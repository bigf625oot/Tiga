from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_config import SystemConfig


class CRUDSystemConfig:
    async def get_by_key(self, db: AsyncSession, key: str) -> Optional[SystemConfig]:
        res = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
        return res.scalars().first()

    async def upsert(self, db: AsyncSession, *, key: str, value: Dict[str, Any], version: int = 1) -> SystemConfig:
        existing = await self.get_by_key(db, key)
        if existing:
            existing.value = value
            existing.version = version
            db.add(existing)
            await db.commit()
            await db.refresh(existing)
            return existing

        obj = SystemConfig(key=key, value=value, version=version)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def delete_by_key(self, db: AsyncSession, key: str) -> bool:
        existing = await self.get_by_key(db, key)
        if not existing:
            return False
        await db.delete(existing)
        await db.commit()
        return True


system_config = CRUDSystemConfig()

