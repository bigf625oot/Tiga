import logging
import json
import re
from typing import AsyncGenerator, Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.core.base_handler import BaseHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.services.eah_agent.core.agent_factory import AgentFactory
from app.services.eah_agent.domain.config import AgentConfig, ToolConfig
from app.models.llm_model import LLMModel
from app.core.i18n import _
from app.core.config import settings
from app.core.shared_state import StateManager, SharedState
from app.core.context_compressor import ContextCompressor
from app.services.eah_agent.storage.session_history import SessionHistory
from app.services.eah_agent.utils.session_kb import SessionKnowledgeManager

from agno.agent import Agent
from agno.tools import Toolkit
# Import DataToolkit
from app.services.eah_agent.tools.libs.data_toolkit import DataToolkit
# Import E2BTools
try:
    from agno.tools.e2b import E2BTools
except ImportError:
    E2BTools = None

logger = logging.getLogger(__name__)

class DataHandler(BaseHandler):
    """
    Handles 'data_query' (SQL) and 'kg_qa' (Knowledge Graph) intents.
    Wraps existing specialized services using Agno Agent with DataToolkit.
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)
        self.agent: Optional[Agent] = None
        # Shared State Management
        self.state_manager = StateManager.get_instance()

    async def _ensure_agent_initialized(self, session_id: str = None, **kwargs):
        """
        Initializes the DataAgent.
        """
        if self.agent and self.llm_model:
            return

        try:
            # 1. Config
            tools = []
            
            # Add DataToolkit
            tools.append(DataToolkit())
            
            # Add E2BTools if configured
            if E2BTools and settings.E2B_API_KEY:
                try:
                    e2b_tool = E2BTools(api_key=settings.E2B_API_KEY)
                    tools.append(e2b_tool)
                except Exception as e:
                    logger.warning(f"Failed to init E2BTools: {e}")
            
            # Add Python/Pandas/CSV tools for local fallback or additional analysis
            # We can use our wrapper tools or Agno's directly. 
            # Let's use generic Python capability if E2B is missing, or just rely on DataToolkit.
            # User requested "Multimodal ability: allow user to upload Excel/CSV".
            # Agno's CsvTools/PandasTools are good for this.
            from app.services.eah_agent.tools.libs.coding_tools import CsvTools, PandasTools
            tools.append(CsvTools())
            tools.append(PandasTools())

            instructions = [
                "You are a Data Analyst Agent.",
                "Your goal is to answer user questions by querying the database or knowledge graph, and analyzing the results.",
                "1. For general data questions, use `query_database` to get SQL, data, and charts.",
                "2. For relationship questions, use `generate_kg_chart`.",
                "3. If the user provides files (CSV/Excel), use pandas/csv tools to analyze them.",
                "4. You can use Python (via E2B or local) to perform advanced analysis or plotting if the database tools are insufficient.",
                "IMPORTANT: If you generate or receive a chart configuration (JSON), you MUST output it in your response wrapped in a special block like this:",
                "::: echarts",
                "{ ... chart json ... }",
                ":::",
                "Do not modify the chart JSON structure."
            ]
            
            config = AgentConfig(
                name="DataAgent",
                role="Data Analyst",
                instructions=instructions,
                tools=[], # We pass instances directly to factory or agent
                reasoning=True, # Enable reasoning as requested
                model_params={"temperature": 0.1} # Low temp for code/data
            )

            # Create Agent
            # Note: AgentFactory usually takes ToolConfig (dicts) or we can instantiate Agent directly.
            # Since we have custom Tool instances (DataToolkit), it's easier to instantiate Agent directly 
            # or extend Factory. BaseHandler doesn't mandate Factory.
            # QuickHandler uses Factory but also appends tools manually.
            
            # Let's use Factory for basic setup then append our tools
            self.agent = await AgentFactory.create_agent(config, llm_model=self.llm_model)
            
            # Inject our instances
            if self.agent:
                self.agent.tools.extend(tools)
                self.agent.monitoring = True

            # Save State
            if session_id:
                state = await self.state_manager.get_state(session_id)
                if not state:
                    state = SharedState(session_id=session_id, mode="data")
                state.agent_config = config
                await self.state_manager.save_state(session_id, state)

        except Exception as e:
            logger.error(f"Failed to init DataAgent: {e}")
            self.agent = None

    async def _process_files(self, files: list, session_id: str) -> str:
        """
        Process uploaded files for analysis.
        Returns context string describing the files.
        """
        from pathlib import Path
        import shutil
        
        context_parts = []
        temp_dir = Path("data/temp") / session_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        for file in files:
            filename = getattr(file, "filename", "unknown")
            try:
                file_path = temp_dir / filename
                with open(file_path, "wb") as buffer:
                    file.file.seek(0)
                    shutil.copyfileobj(file.file, buffer)
                
                context_parts.append(f"Uploaded file: {filename} (Path: {file_path})")
                # We could load into Pandas here or just tell the agent the path
            except Exception as e:
                logger.error(f"File upload failed: {e}")
        
        return "\n".join(context_parts)

    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        db = kwargs.get("db")
        session_id = kwargs.get("session_id")
        files = kwargs.get("files")
        
        await self._ensure_agent_initialized(session_id=session_id)
        
        if not self.agent:
            yield {"type": "error", "content": _("DataAgent initialization failed.")}
            return

        # 1. Handle Files
        if files and session_id:
            yield {"type": "status", "content": _("Processing uploaded files...")}
            file_context = await self._process_files(files, session_id)
            if file_context:
                input_text += f"\n\n[Context]\n{file_context}\nYou can access these files using pandas at the provided paths."

        # 2. Context Compression & History
        history_messages = []
        if db and session_id:
            try:
                history = SessionHistory(db)
                msgs = await history.get_messages(session_id, limit=10) # Data queries are heavy, keep limit low
                raw_history = [{"role": m.role, "content": m.content} for m in msgs]
                
                compressor = ContextCompressor(model=self.llm_model)
                history_messages = await compressor.compress_context(raw_history, max_tokens=3000)
            except Exception as e:
                logger.warning(f"History load/compress failed: {e}")

        # 3. Run Agent
        try:
            yield {"type": "status", "content": _("Analyzing data request...")}
            
            # Using run_kwargs to pass history
            run_kwargs = {"messages": history_messages, "stream": True}
            
            response_stream = await self.agent.arun(input_text, **run_kwargs)
            
            buffer = ""
            
            async for chunk in response_stream:
                # Tool Status
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    tool_names = [tc.function.name for tc in chunk.tool_calls if tc.function]
                    if tool_names:
                        yield {"type": "status", "content": f"Running tools: {', '.join(tool_names)}..."}

                # Reasoning (Think)
                reasoning = getattr(chunk, "reasoning", None) or getattr(chunk, "reasoning_content", None)
                if reasoning:
                    yield {"type": "think", "content": reasoning}

                # Content & Chart Detection
                content = getattr(chunk, "content", None)
                if content:
                    # Accumulate for pattern matching if needed, but for streaming we usually just yield
                    # However, to detect the chart block reliably, we might need to parse the buffer.
                    # Simple approach: Yield content as is, but also look for the pattern.
                    # Since we are yielding to frontend, frontend handles markdown.
                    # BUT the requirement says: yield {"type": "chart", "content": ...}
                    # So we MUST intercept the chart JSON.
                    
                    buffer += content
                    
                    # Regex for ::: echarts { ... } :::
                    # Note: This is tricky in streaming. We might process it line by line or use a state machine.
                    # For simplicity, we check if the buffer contains the full block, extract it, yield 'chart', 
                    # and remove it from the 'content' yield? 
                    # Or just yield it as content and ALSO as chart? 
                    # Usually 'chart' type triggers a specific UI widget.
                    # Let's try to extract it.
                    
                    chart_pattern = re.compile(r":::\s*echarts\s*(\{[\s\S]*?\})\s*:::", re.MULTILINE)
                    match = chart_pattern.search(buffer)
                    if match:
                        chart_json_str = match.group(1)
                        try:
                            chart_data = json.loads(chart_json_str)
                            yield {"type": "chart", "content": chart_data}
                            # Remove the chart block from buffer/output to avoid duplication? 
                            # Or keep it for history?
                            # Usually we keep it.
                            # We reset buffer after match to avoid re-matching
                            buffer = buffer.replace(match.group(0), "") 
                        except json.JSONDecodeError:
                            pass
                    
                    yield {"type": "content", "content": content}
                    
                elif isinstance(chunk, str):
                    yield {"type": "content", "content": chunk}

        except Exception as e:
            logger.error(f"DataAgent run failed: {e}")
            yield {"type": "error", "content": _("An error occurred during data analysis.")}
