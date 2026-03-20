import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


@pytest.mark.asyncio
async def test_service_market_installed_roundtrip():
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

            user_id = str(uuid.uuid4())
            skill_id = str(uuid.uuid4())
            mcp_id = str(uuid.uuid4())

            from app.models.user import User
            from app.models.skill import Skill
            from app.models.mcp import MCPServer, MCPTransportType
            from app.api.endpoints.service_market import install_item, list_installed, uninstall_item
            from app.schemas.service_market import MarketInstallRequest

            async with SessionLocal() as db:
                db.add(User(id=user_id, username="u1", email="u1@example.com"))
                db.add(
                    Skill(
                        id=skill_id,
                        slug="test-skill",
                        name="Test Skill",
                        description="desc",
                        version="1.0.0",
                        is_active=True,
                    )
                )
                db.add(
                    MCPServer(
                        id=mcp_id,
                        slug="test-mcp",
                        name="Test MCP",
                        description="desc",
                        version="1.0.0",
                        transport_type=MCPTransportType.STDIO,
                        config={},
                        is_active=True,
                    )
                )
                await db.commit()

            async with SessionLocal() as db:
                r1 = await install_item(payload=MarketInstallRequest(type="skill", id=skill_id), user_id=user_id, db=db)
                assert r1 == {"ok": True}
                r2 = await install_item(payload=MarketInstallRequest(type="mcp", id=mcp_id), user_id=user_id, db=db)
                assert r2 == {"ok": True}

            async with SessionLocal() as db:
                installed = await list_installed(user_id=user_id, db=db)
                assert skill_id in installed["skill"]
                assert mcp_id in installed["mcp"]

            async with SessionLocal() as db:
                r3 = await uninstall_item(item_type="skill", item_id=skill_id, user_id=user_id, db=db)
                assert r3 == {"ok": True}

            async with SessionLocal() as db:
                installed2 = await list_installed(user_id=user_id, db=db)
                assert skill_id not in installed2["skill"]
                assert mcp_id in installed2["mcp"]
        finally:
            await engine.dispose()

