import logging
import time
from typing import Any, Callable, Generator, List, Optional, AsyncGenerator

import pandas as pd
from agno.agent import Agent
from sqlalchemy import text

from app.core.config import settings
from app.services.llm.factory import ModelFactory

from .models import DbConnectionConfig
from .runners.sql_runner import SQLAlchemyRunner
from .tools.run_sql import RunSqlTool
from .tools.visualize_data import VisualizeDataTool

# Configure logger
logger = logging.getLogger(__name__)


class SmartDataQueryService:
    _instance = None

    def __init__(self):
        self.agent: Optional[Agent] = None
        self.sql_runner: Optional[SQLAlchemyRunner] = None
        self.current_db_config: Optional[DbConnectionConfig] = None
        self.last_run_df: Optional[pd.DataFrame] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _build_connection_string_and_args(self, config: DbConnectionConfig):
        conn_str = ""
        connect_args = {}

        # Base arguments
        if config.timeout and config.type != "sqlite":
            # SQLAlchemy uses 'connect_timeout' for most dialects in connect_args
            connect_args["connect_timeout"] = config.timeout
            logger.debug(f"Set connect_timeout to {config.timeout}")

        if config.type == "sqlite":
            # Handle path, assume relative to project or absolute
            conn_str = f"sqlite:///{config.path}"
        elif config.type == "postgresql":
            # Using standard driver
            conn_str = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"
            if config.ssl_mode and config.ssl_mode != "disable":
                connect_args["sslmode"] = config.ssl_mode
            if config.db_schema:
                connect_args["options"] = f"-c search_path={config.db_schema}"
        elif config.type == "mysql":
            # [Fix] URL encode password and host to handle special characters like # or @
            import urllib.parse

            safe_password = urllib.parse.quote_plus(config.password)
            safe_host = urllib.parse.quote_plus(config.host)
            # Host typically doesn't need encoding unless it has weird chars, but password definitely does.
            # However, if host contains #, it breaks SQLAlchemy URL parsing.

            # Reconstruct connection string carefully
            conn_str = f"mysql+pymysql://{config.user}:{safe_password}@{safe_host}:{config.port}/{config.database}"
            if config.charset:
                connect_args["charset"] = config.charset

        return conn_str, connect_args

    def connect_db(self, config: DbConnectionConfig):
        """
        Connect to a database based on configuration.
        """
        logger.info(f"Configuring database connection for {config.type}...")

        conn_str, connect_args = self._build_connection_string_and_args(config)

        logger.info("Initializing SQLAlchemy Runner...")
        # Initialize Runner with extra args
        try:
            self.sql_runner = SQLAlchemyRunner(
                conn_str, connect_args=connect_args, pool_size=config.pool_size or 5, max_overflow=10
            )
            self.current_db_config = config
            logger.info("SQLAlchemy engine created.")
        except Exception as e:
            logger.error(f"Failed to create engine: {e}")
            raise e

        # Test connection immediately
        # We run a simple query to verify
        logger.info("Testing connection with 'SELECT 1'...")
        start_test = time.time()
        try:
            with self.sql_runner.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            duration = (time.time() - start_test) * 1000
            logger.info(f"Connection test passed in {duration:.2f}ms")
        except Exception as e:
            # Reset runner on failure
            duration = (time.time() - start_test) * 1000
            logger.error(f"Connection test failed after {duration:.2f}ms: {e}")
            self.sql_runner = None
            raise e

        # Reset state
        self.last_run_df = None

    def test_connection(self, config: DbConnectionConfig) -> bool:
        """
        Test a database connection without persisting it.
        """
        try:
            conn_str, connect_args = self._build_connection_string_and_args(config)

            # Create a temporary engine
            # We use a small pool or NullPool for testing
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

    def _create_agent_tools(self) -> List[Callable]:
        """
        Create tool functions for the Agent.
        """
        if not self.sql_runner:
            return []

        run_sql_tool = RunSqlTool(self.sql_runner)
        visualize_tool = VisualizeDataTool()

        def run_sql(sql: str) -> str:
            """
            Executes a SQL query against the connected database.
            Args:
                sql: The SQL query to execute.
            Returns:
                A markdown representation of the first 10 rows of the result.
            """
            try:
                df = run_sql_tool.execute(sql)
                self.last_run_df = df
                if df.empty:
                    return "Query executed successfully but returned no results."
                return df.head(10).to_markdown()
            except Exception as e:
                return f"Error executing SQL: {str(e)}"

        def visualize_data(question: str = "") -> str:
            """
            Generates a visualization (chart) based on the last executed query results.
            Args:
                question: The question or title for the chart.
            Returns:
                A JSON string representing the Plotly chart, or a message if generation fails.
            """
            if self.last_run_df is None or self.last_run_df.empty:
                return "No data available to visualize. Please run a SQL query first."

            result = visualize_tool.execute(self.last_run_df, question)
            if result:
                return f"Chart generated: {result}"  # The frontend needs to parse this
            return "Could not generate a suitable chart for this data."

        return [run_sql, visualize_data]

    def _init_agent(self, llm_model=None):
        """
        Initialize the Agno Agent.
        """
        tools = self._create_agent_tools()
        if not tools:
            return

        instructions = [
            "You are an expert Data Analyst.",
            "Your goal is to answer the user's question by querying the connected database.",
            "Process:",
            "1.  Analyze the user's question and the database schema (if known).",
            "2.  Generate a valid SQL query.",
            "3.  Execute the query using `run_sql`.",
            "4.  Analyze the results returned.",
            "5.  If the user asks for a chart or the data is suitable for visualization, use `visualize_data`.",
            "6.  Provide a concise summary of the answer.",
            "Important:",
            " - Always use `run_sql` to get data. Do not guess.",
            " - If the query fails, try to fix the SQL and retry.",
            " - If `visualize_data` returns a JSON string, output it as is in a separate block or mention a chart was created.",
            " - When outputting the chart JSON, wrap it in a custom tag <vanna-chart>JSON_HERE</vanna-chart> so the frontend can render it.",
        ]

        # Model Selection
        model = None
        if llm_model:
            model = ModelFactory.create_model(llm_model)
        elif self.agent and self.agent.model:
            model = self.agent.model
        else:
            # Fallback
            from agno.models.openai import OpenAIChat

            model = OpenAIChat(id="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY or "dummy")

        self.agent = Agent(
            name="SmartDataQueryAgent",
            model=model,
            tools=tools,
            instructions=instructions,
            markdown=True,
            show_tool_calls=True,
            reasoning=True,  # Enable reasoning if model supports it
        )

    async def query(self, question: str, llm_model=None) -> AsyncGenerator[Any, None]:
        """
        Run the agent to answer a question.
        """
        if not self.sql_runner:
            yield "Please connect to a database first."
            return

        # Re-init agent if needed (e.g. to update tools or model)
        # For simplicity, we re-init if model changes or agent missing
        if not self.agent or llm_model:
            self._init_agent(llm_model)

        if not self.agent:
            yield "Agent initialization failed."
            return

        try:
            # Running in async generator keeps execution in the main event loop
            response_stream = self.agent.run(question, stream=True)
            for chunk in response_stream:
                if hasattr(chunk, "content"):
                    yield chunk.content
                else:
                    yield str(chunk)
        except Exception as e:
            yield f"Error during query: {str(e)}"


data_query_service = SmartDataQueryService.get_instance()
