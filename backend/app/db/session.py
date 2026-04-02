from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# SQLite 默认使用 QueuePool，配合 WAL 模式和 busy_timeout 即可很好地处理并发。
# 不要使用 StaticPool，因为它会在多个异步请求间共享同一个连接，导致事务状态混乱（如 rollback 串线）。
_engine_kwargs = {"echo": False}
if "sqlite" in settings.database_url:
    # 增加 timeout 防止 database is locked
    _engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 15}
    # 使用默认的 QueuePool 或 NullPool，不要用 StaticPool
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **_engine_kwargs)

# 针对 SQLite 的特殊优化
if "sqlite" in settings.database_url:

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 防御外部工具（如 DB Browser）并发读写时的锁等待
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
