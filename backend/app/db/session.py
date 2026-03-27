from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 针对 SQLite 的并发写冲突，必须在 connect_args 层面配置 timeout，
# 而非 PRAGMA busy_timeout —— aiosqlite 在 PRAGMA 执行前已创建连接，
# connect_args 的 timeout 参数直接作用于底层 sqlite3 模块的写锁等待。
_engine_kwargs = {"echo": False}
if "sqlite" in settings.database_url:
    # timeout=30: 写锁被占用时最多等待 30 秒再报 OperationalError，
    # 彻底消除流式响应期间并发写导致的 "database is locked" 错误。
    _engine_kwargs["connect_args"] = {"timeout": 30, "check_same_thread": False}

engine = create_async_engine(settings.database_url, **_engine_kwargs)

# 针对 SQLite 的特殊优化
if "sqlite" in settings.database_url:

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        # busy_timeout 双保险：PRAGMA 层也设置，与 connect_args timeout 共同生效
        cursor.execute("PRAGMA busy_timeout=30000")
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
