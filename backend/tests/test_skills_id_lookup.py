import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


@pytest.mark.asyncio
async def test_skills_endpoints_can_lookup_string_id_with_uuid_param():
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
        engine = create_async_engine(database_url)
        try:
            from app.db.base import Base
            from app.models.loader import import_all_models

            import_all_models()

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

            skill_uuid = uuid.uuid4()

            from app.models.skill import Skill

            async with SessionLocal() as db:
                db.add(
                    Skill(
                        id=str(skill_uuid),
                        slug="test-skill",
                        name="Test Skill",
                        description="desc",
                        version="1.0.0",
                    )
                )
                await db.commit()

            from app.api.endpoints.skills import delete_skill, read_skill, update_skill
            from app.schemas.skill import SkillUpdate

            async with SessionLocal() as db:
                skill = await read_skill(skill_id=skill_uuid, db=db)
                assert skill.id == str(skill_uuid)

            async with SessionLocal() as db:
                updated = await update_skill(
                    skill_id=skill_uuid,
                    skill_update=SkillUpdate(name="Updated Skill"),
                    db=db,
                )
                assert updated.id == str(skill_uuid)
                assert updated.name == "Updated Skill"

            async with SessionLocal() as db:
                result = await delete_skill(skill_id=skill_uuid, db=db)
                assert result == {"ok": True}
        finally:
            await engine.dispose()
