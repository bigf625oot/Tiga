import logging
import time
import json
import uuid
from typing import Any, Callable, Generator, List, Optional, AsyncGenerator, Dict

import pandas as pd
from sqlalchemy import text, inspect, select, update, delete, desc, func
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.llm_model import LLMModel
from app.models.data_query_session import DataQuerySession, DataQueryMessage
from .models import DbConnectionConfig
from .runners.sql_runner import SQLAlchemyRunner
from .core import VannaCore
from app.services.rag.engines.lightrag import lightrag_engine

# Configure logger
logger = logging.getLogger(__name__)


class SmartDataQueryService:
    _instance = None

    def __init__(self):
        self.vanna_core = VannaCore()
        self.current_db_config: Optional[DbConnectionConfig] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # --- Session Management ---

    async def create_session(self, title: str = "New Chat", user_id: str = "default_user") -> DataQuerySession:
        async with AsyncSessionLocal() as session:
            new_session = DataQuerySession(
                id=str(uuid.uuid4()),
                title=title,
                user_id=user_id
            )
            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)
            return new_session

    async def get_session(self, session_id: str) -> Optional[DataQuerySession]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DataQuerySession).filter(DataQuerySession.id == session_id, DataQuerySession.is_deleted == False)
            )
            return result.scalars().first()

    async def list_sessions(self, user_id: str = "default_user", status: str = "active", limit: int = 20, offset: int = 0) -> List[DataQuerySession]:
        async with AsyncSessionLocal() as session:
            query = select(DataQuerySession).filter(
                DataQuerySession.user_id == user_id, 
                DataQuerySession.is_deleted == False
            )
            
            if status == "archived":
                query = query.filter(DataQuerySession.is_archived == True)
            else:
                query = query.filter(DataQuerySession.is_archived == False)
                
            # Order by pinned first, then updated_at desc
            query = query.order_by(desc(DataQuerySession.is_pinned), desc(DataQuerySession.updated_at)).limit(limit).offset(offset)
            
            result = await session.execute(query)
            return result.scalars().all()

    async def update_session(self, session_id: str, **kwargs) -> Optional[DataQuerySession]:
        async with AsyncSessionLocal() as session:
            stmt = update(DataQuerySession).where(DataQuerySession.id == session_id).values(**kwargs)
            await session.execute(stmt)
            await session.commit()
            return await self.get_session(session_id)

    async def delete_session(self, session_id: str, hard: bool = False):
        async with AsyncSessionLocal() as session:
            if hard:
                stmt = delete(DataQuerySession).where(DataQuerySession.id == session_id)
            else:
                stmt = update(DataQuerySession).where(DataQuerySession.id == session_id).values(is_deleted=True)
            await session.execute(stmt)
            await session.commit()

    async def add_message(self, session_id: str, role: str, content: str, sql: str = None, chart: dict = None, error: str = None):
        async with AsyncSessionLocal() as session:
            msg = DataQueryMessage(
                session_id=session_id,
                role=role,
                content=content,
                sql_query=sql,
                chart_config=chart,
                error_message=error
            )
            session.add(msg)
            
            # Update session timestamp
            await session.execute(
                update(DataQuerySession)
                .where(DataQuerySession.id == session_id)
                .values(updated_at=func.now()) # func needs import or use datetime
            )
            await session.commit()
            return msg
            
    async def get_messages(self, session_id: str) -> List[DataQueryMessage]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DataQueryMessage)
                .filter(DataQueryMessage.session_id == session_id)
                .order_by(DataQueryMessage.created_at.asc())
            )
            return result.scalars().all()

    # --- End Session Management ---

    async def _get_llm_config(self):
        """Fetch active LLM configuration from database."""
        async with AsyncSessionLocal() as session:
            # 1. Get Chat Model
            result_chat = await session.execute(
                select(LLMModel)
                .filter(LLMModel.is_active == True, LLMModel.model_type != "embedding")
                .order_by(LLMModel.updated_at.desc())
            )
            chat_model = result_chat.scalars().first()
            
            # 2. Get Embedding Model
            result_embed = await session.execute(
                select(LLMModel)
                .filter(LLMModel.is_active == True, LLMModel.model_type == "embedding")
                .order_by(LLMModel.updated_at.desc())
            )
            embed_model = result_embed.scalars().first()

            if not chat_model or not chat_model.api_key:
                # Fallback to settings
                if settings.OPENAI_API_KEY:
                    logger.info("No active chat model found in DB, using settings.OPENAI_API_KEY")
                    return (
                        settings.OPENAI_API_KEY, 
                        getattr(settings, "OPENAI_BASE_URL", None), 
                        "gpt-3.5-turbo",
                        None, None, None # No specific embedding config, will use defaults
                    )
                raise ValueError("No active LLM model found. Please configure a model in System Settings.")

            return (
                chat_model.api_key, 
                chat_model.base_url, 
                chat_model.model_id,
                embed_model.api_key if embed_model else None,
                embed_model.base_url if embed_model else None,
                embed_model.model_id if embed_model else None
            )

    def _build_connection_string_and_args(self, config: DbConnectionConfig):
        conn_str = ""
        connect_args = {}

        # Base arguments
        if config.timeout and config.type != "sqlite":
            connect_args["connect_timeout"] = config.timeout

        if config.type == "sqlite":
            conn_str = f"sqlite:///{config.path}"
        elif config.type == "postgresql":
            conn_str = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"
            if config.ssl_mode and config.ssl_mode != "disable":
                connect_args["sslmode"] = config.ssl_mode
            if config.db_schema:
                connect_args["options"] = f"-c search_path={config.db_schema}"
        elif config.type == "mysql":
            import urllib.parse
            safe_password = urllib.parse.quote_plus(config.password)
            safe_host = urllib.parse.quote_plus(config.host)
            conn_str = f"mysql+pymysql://{config.user}:{safe_password}@{safe_host}:{config.port}/{config.database}"
            if config.charset:
                connect_args["charset"] = config.charset

        return conn_str, connect_args

    async def connect_db(self, config: DbConnectionConfig):
        """
        Connect to a database and train Vanna.
        Async wrapper that handles LLM config and offloads sync work.
        """
        # 1. Configure LLM first
        try:
            (
                chat_api_key, chat_base_url, chat_model_id,
                embed_api_key, embed_base_url, embed_model_id
            ) = await self._get_llm_config()
            
            self.vanna_core.configure_llm(
                api_key=chat_api_key, 
                base_url=chat_base_url, 
                model=chat_model_id,
                embedding_api_key=embed_api_key,
                embedding_base_url=embed_base_url,
                embedding_model=embed_model_id
            )
        except Exception as e:
            logger.error(f"Failed to configure LLM: {e}")
            raise e

        # 2. Run sync connection logic in threadpool
        await run_in_threadpool(self._connect_and_train_sync, config)

    def _connect_and_train_sync(self, config: DbConnectionConfig):
        """
        Synchronous part of connection and training.
        """
        logger.info(f"Configuring database connection for {config.type}...")

        conn_str, connect_args = self._build_connection_string_and_args(config)

        try:
            sql_runner = SQLAlchemyRunner(
                conn_str, connect_args=connect_args, pool_size=config.pool_size or 5, max_overflow=10
            )
            self.vanna_core.set_sql_runner(sql_runner)
            self.current_db_config = config
            logger.info("SQLAlchemy engine created.")
            
            # Auto-Train (Extract Schema)
            # Wrap in try-except to prevent blocking connection if embedding/vector-db fails
            try:
                self._train_on_schema(sql_runner)
            except Exception as e:
                logger.error(f"Schema training failed (non-critical): {e}. You can still query the database, but RAG context might be incomplete.")
            
        except Exception as e:
            logger.error(f"Failed to connect/train: {e}")
            raise e

    def _train_on_schema(self, runner: SQLAlchemyRunner):
        """Extract DDL and train Vanna."""
        logger.info("Starting schema extraction and training...")
        
        # Clear existing vector data to avoid dimension mismatch or stale schema
        self.vanna_core.reset_vector_store()
        
        inspector = inspect(runner.engine)
        ddl_statements = []
        
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            # Simplified DDL generation
            col_defs = []
            for col in columns:
                col_defs.append(f"{col['name']} {col['type']}")
            ddl = f"CREATE TABLE {table_name} ({', '.join(col_defs)});"
            ddl_statements.append(ddl)
            
        # Train Vanna
        for ddl in ddl_statements:
            self.vanna_core.train(ddl=ddl)
        logger.info(f"Trained on {len(ddl_statements)} tables.")

    def test_connection(self, config: DbConnectionConfig) -> bool:
        try:
            conn_str, connect_args = self._build_connection_string_and_args(config)
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool
            engine = create_engine(conn_str, connect_args=connect_args, poolclass=NullPool)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            engine.dispose()
            return True
        except Exception as e:
            logger.error(f"Test connection failed: {e}")
            return False

    async def query(self, question: str, session_id: Optional[str] = None, llm_model=None) -> AsyncGenerator[Any, None]:
        """
        运行 Tiga 查询并以流式返回结果。
        """
        step_id = 1
        
        def wrap_msg(content: str, type_: str = "process") -> str:
            nonlocal step_id
            msg_obj = {
                "step": step_id,
                "content": content,
                "type": type_
            }
            step_id += 1
            return json.dumps(msg_obj, ensure_ascii=False) + "\n"

        if not self.vanna_core.sql_runner:
            yield wrap_msg("请先连接到数据库。", "error")
            return

        # 保存用户消息
        if session_id:
            try:
                await self.add_message(session_id, "user", question)
            except Exception as e:
                logger.error(f"保存用户消息失败：{e}")

        full_content = []
        generated_sql = None
        generated_chart = None
        error_msg = None

        try:
            # 1. 意图识别
            msg = "1.1.正在分析问题与意图...\n\n"
            yield wrap_msg(msg, "process")
            
            intent = self.vanna_core.classify_intent(question)
            msg = f"> **1.2.识别到意图**: {intent}\n\n"
            yield wrap_msg(msg, "process")

            # 2. 生成 SQL
            msg = "2.正在生成 SQL...\n"
            yield wrap_msg(msg, "process")
            
            sql = self.vanna_core.generate_sql(question)
            generated_sql = sql
            
            # Extract pure SQL for frontend state, but send block for display if needed (or just send pure SQL?)
            # The frontend currently expects the block in the 'content' for SQL view if we were using content,
            # but we are moving to structured types.
            # Let's send the markdown block as 'sql' type so it can be rendered if needed, 
            # or frontend can strip backticks.
            msg = f"```sql\n{sql}\n```\n\n"
            yield wrap_msg(msg, "sql")
            
            if sql.startswith("--"):
                msg = "抱歉，未能生成有效的 SQL 查询。"
                yield wrap_msg(msg, "error")
                full_content.append(msg) # Keep error in content
                return

            msg = "正在执行查询...\n\n"
            yield wrap_msg(msg, "process")
            
            # 3. 执行 SQL
            logger.info(f"审计：用户问题 '{question}' 执行的 SQL：{sql}")
            df = self.vanna_core.run_sql(sql)
            
            if df.empty:
                msg = "查询已执行，但未返回结果。"
                yield wrap_msg(msg, "process")
                full_content.append(msg)
                return
                
            # 4. 数据预览
            msg_header = f"### 查询结果（{len(df)} 行）\n"
            yield wrap_msg(msg_header, "data")
            full_content.append(msg_header)
            
            msg_table = df.head(10).to_markdown() + "\n\n"
            yield wrap_msg(msg_table, "data")
            full_content.append(msg_table)
            
            # 5. 生成图表
            msg = "正在生成可视化...\n"
            yield wrap_msg(msg, "process")
            
            chart = self.vanna_core.generate_echarts(question, df, sql)
            generated_chart = chart
            
            if chart:
                # 使用特殊块供前端解析
                msg = f"\n::: echarts\n{json.dumps(chart, indent=2)}\n:::\n"
                yield wrap_msg(msg, "chart")
                full_content.append(msg)
            
        except Exception as e:
            error_msg = str(e)
            yield wrap_msg(f"错误：{str(e)}", "error")
        finally:
            # 保存助手消息
            if session_id:
                try:
                    await self.add_message(
                        session_id=session_id, 
                        role="assistant", 
                        content="".join(full_content),
                        sql=generated_sql,
                        chart=generated_chart,
                        error=error_msg
                    )
                except Exception as e:
                    logger.error(f"保存助手消息失败：{e}")

    def get_tables(self) -> List[str]:
        if not self.vanna_core.sql_runner:
            raise Exception("数据库未连接")
        return self.vanna_core.sql_runner.get_tables()

    def get_table_data(self, table_name: str, limit: int = 100, offset: int = 0) -> dict:
        if not self.vanna_core.sql_runner:
            raise Exception("数据库未连接")
        
        if not table_name.replace("_", "").isalnum():
             raise Exception("无效的表名")

        sql = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
        df = self.vanna_core.sql_runner.run_sql(sql)
        
        data = df.to_dict(orient='split')
        return {
            "columns": data["columns"],
            "data": data["data"],
            "total": len(df)
        }

    async def convert_table_to_graph_task(self, job_id: str, table_name: str, update_status_callback: Callable):
        try:
            update_status_callback(job_id, "running", 10, "正在获取表数据...")
            
            # 获取数据 (限制50条用于演示)
            limit = 50 
            # 在线程池中运行以避免阻塞事件循环
            data = await run_in_threadpool(self.get_table_data, table_name, limit=limit)
            rows = data.get("data", [])
            cols = data.get("columns", [])
            
            if not rows:
                update_status_callback(job_id, "completed", 100, "表为空，无需转换")
                return

            update_status_callback(job_id, "running", 30, f"正在分析 {len(rows)} 条数据...")
            
            # 构建文本
            text_parts = []
            for idx, row in enumerate(rows):
                # 简单的行转文本逻辑
                row_str = ", ".join([f"{k}:{v}" for k, v in zip(cols, row)])
                text_parts.append(f"数据表记录 #{idx+1}：{row_str}")
            
            full_text = f"以下是数据库表【{table_name}】的数据记录，请构建相关实体和关系：\n\n" + "\n".join(text_parts)
            
            update_status_callback(job_id, "running", 50, "正在构建知识图谱（这可能需要一些时间）...")
            
            # 确保 LightRAG 已初始化
            async with AsyncSessionLocal() as session:
                await lightrag_engine.ensure_initialized(session)
            
            # 插入文本建立索引和图谱
            await lightrag_engine.insert_text_async(full_text, description=f"Database Table: {table_name}")
            
            update_status_callback(job_id, "completed", 100, "转换成功！")
            
        except Exception as e:
            logger.error(f"转换图谱任务失败: {e}")
            update_status_callback(job_id, "failed", 0, f"转换失败: {str(e)}")

data_query_service = SmartDataQueryService.get_instance()
