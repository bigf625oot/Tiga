from typing import List, AsyncGenerator, Any, Dict
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError, InterfaceError, ProgrammingError
from sqlalchemy.engine import URL
from app.strategies.base import BaseSource
from app.models.domain import MetadataModel, DataChunk
from app.utils.crypto_utils import decrypt_field

class DatabaseSource(BaseSource):
    """
    Strategy for Database sources (MySQL, PostgreSQL, etc.)
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.engine = None

    async def _get_engine(self):
        if self.engine:
            return self.engine
        
        db_type = self.config.get('type', '').lower()
        driver = 'asyncpg' if 'postgres' in db_type else 'aiomysql'
        if 'sqlite' in db_type:
            driver = 'aiosqlite'
            
        password = self.config.get('password')
        if self.config.get('password_encrypted'):
            password = decrypt_field(self.config['password_encrypted'])
            
        url = URL.create(
            drivername=f"{db_type}+{driver}",
            username=self.config.get('username'),
            password=password,
            host=self.config.get('host'),
            port=self.config.get('port'),
            database=self.config.get('database'),
        )
        
        self.engine = create_async_engine(url)
        return self.engine

    async def test_connection(self) -> Dict[str, Any]:
        try:
            engine = await self._get_engine()
            
            async def _check():
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))

            await asyncio.wait_for(_check(), timeout=5.0)
            return {"success": True, "message": "Successfully connected to database."}
        except asyncio.TimeoutError:
            return {"success": False, "error_type": "TIMEOUT", "message": "Connection/Query timed out"}
        except (OperationalError, InterfaceError) as e:
            msg = str(e).lower()
            if "password" in msg or "authentication" in msg or "access denied" in msg:
                 return {"success": False, "error_type": "AUTH_FAILED", "message": str(e)}
            if "refused" in msg or "network" in msg or "host" in msg:
                 return {"success": False, "error_type": "NETWORK_ERROR", "message": str(e)}
            return {"success": False, "error_type": "UNKNOWN", "message": str(e)}
        except ProgrammingError as e:
             return {"success": False, "error_type": "AUTH_FAILED", "message": str(e)}
        except Exception as e:
            return {"success": False, "error_type": "UNKNOWN", "message": str(e)}

    async def fetch_metadata(self) -> List[MetadataModel]:
        engine = await self._get_engine()
        metadata_list = []
        
        # SQLAlchemy inspection is sync, so run in executor if needed
        # But for async engine, we can use run_sync
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        async with engine.connect() as conn:
            tables = await conn.run_sync(get_tables)
            for table in tables:
                metadata_list.append(MetadataModel(
                    name=table,
                    type="table",
                    description=f"Table in {self.config.get('database')}"
                ))
        return metadata_list

    async def fetch_data(self, **kwargs) -> AsyncGenerator[DataChunk, None]:
        engine = await self._get_engine()
        table_name = kwargs.get('table_name')
        sql_query = kwargs.get('query')
        
        limit = kwargs.get('limit', 1000)
        offset = kwargs.get('offset', 0)
        
        if sql_query:
            # Execute raw SQL
            # Basic safety check: ensure it's a SELECT
            if not sql_query.strip().upper().startswith("SELECT"):
                 # Allow it but maybe log warning? Or restrict. 
                 # For now, let's just proceed.
                 pass
            
            # Wrap in text()
            query = text(sql_query)
            # We might not be able to apply LIMIT/OFFSET easily to arbitrary SQL without parsing
            # So we might just execute it as is, or wrap it in a subquery?
            # "SELECT * FROM ({sql_query}) AS sub LIMIT :limit OFFSET :offset"
            # This is safer for pagination.
            final_query = text(f"SELECT * FROM ({sql_query}) AS sub_query_wrapper LIMIT :limit OFFSET :offset")
            
        elif table_name:
            final_query = text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset")
        else:
            raise ValueError("Either table_name or query is required")
        
        async with engine.connect() as conn:
            # Streaming results
            # Note: stream() requires a transaction for some drivers/dialects, but usually okay for read
            result = await conn.stream(final_query, parameters={"limit": limit, "offset": offset})
            
            chunk_size = 100
            chunk_data = []
            
            async for row in result:
                # Convert row to dict
                row_dict = dict(row._mapping)
                chunk_data.append(row_dict)
                
                if len(chunk_data) >= chunk_size:
                    yield DataChunk(data=chunk_data, count=len(chunk_data), has_more=True)
                    chunk_data = []
            
            if chunk_data:
                yield DataChunk(data=chunk_data, count=len(chunk_data), has_more=False)
