"""
Quick Handler:
Handles 'quick' intent: fast Q&A, chit-chat, simple queries.
是一种特殊的Agent，用于处理用户简单的查询和互动。本质就是reasoning = True/False，默认False。
核心功能：
1. 快速响应用户简单查询（如“你好”、“天气”等）。
2. 支持异步操作，确保在高并发场景下的响应速度。
3. 提供基础的错误处理机制，避免系统崩溃。
"""

import logging
from typing import AsyncGenerator, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.core.base_handler import BaseHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.services.eah_agent.core.agent_factory import AgentFactory
from app.core.config import settings
from app.services.eah_agent.domain.config import AgentConfig, ToolConfig
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor
from app.core.i18n import _
from app.models.llm_model import LLMModel
from app.services.eah_agent.utils.session_kb import SessionKnowledgeManager
from app.core.shared_state import StateManager, SharedState
from agno.agent import Agent

logger = logging.getLogger(__name__)

# Import tools for dynamic loading
try:
    from app.services.rag.mcp_server import search_knowledge_base, query_knowledge_graph

    HAS_KNOWLEDGE_TOOLS = True
except ImportError:
    HAS_KNOWLEDGE_TOOLS = False
    logger.warning("Knowledge base tools not found. RAG features will be disabled.")


class QuickHandler(BaseHandler):
    """
    Handles 'chat' intent: fast Q&A, chit-chat, simple queries.
    Upgraded to use AgnoAgent for history and basic RAG support.
    """

    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)
        self.agent: Optional[Agent] = None
        self._reasoning_enabled: Optional[bool] = None

    async def _ensure_agent_initialized(
        self, db: Optional[AsyncSession] = None, session_id: str = None, **kwargs
    ):
        """
        Initializes the Agno Agent.
        Tries to load configuration from Redis SharedState first.
        """
        desired_reasoning = bool(kwargs.get("enable_reasoning", False))
        if self.agent and self.llm_model and self._reasoning_enabled == desired_reasoning:
            return
        if self.agent and self.llm_model and self._reasoning_enabled != desired_reasoning:
            self.agent = None

        try:
            state_manager = StateManager.get_instance()
            shared_state = None

            # 1. Try to load existing state
            if session_id:
                try:
                    shared_state = await state_manager.get_state(session_id)
                except Exception as e:
                    logger.warning(
                        f"Failed to load shared state for session {session_id} (Redis down?): {e}"
                    )
                    shared_state = None

            config = None

            # 2. Use existing config if available (State Restoration)
            if shared_state and shared_state.agent_config:
                # Map SharedState config back to AgentConfig
                # Note: SharedState might store a slightly different structure depending on implementation
                # Here we assume compatibility or just use it as reference
                # For simplicity, we re-create config based on kwargs but respect mode
                pass

            # 3. Create New Config (if not restored)
            if not config:
                enable_search = kwargs.get("enable_search", True)

                tools = []
                instructions = ["Answer directly.", "Be polite."]
                if desired_reasoning:
                    instructions.append("Write your private reasoning inside <think>...</think> and then write the final answer outside of it.")

                # Configure Tools
                if enable_search:
                    # Check for Tavily
                    if settings.TAVILY_API_KEY:
                        tools.append(ToolConfig(name="tavily", config={"api_key": settings.TAVILY_API_KEY}, enabled=True))
                        instructions.append(
                            "Use the 'tavily' search tool if the user asks for current events or information not in your knowledge."
                        )
                    else:
                        # Fallback to DuckDuckGo with proxy support
                        ddg_config = {}
                        import os
                        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
                        if proxy:
                            ddg_config["proxy"] = proxy
                        
                        tools.append(ToolConfig(name="duckduckgo", config=ddg_config, enabled=True))
                        instructions.append(
                            "Use the search tool if the user asks for current events or information not in your knowledge."
                        )

                config = AgentConfig(
                    name="QuickAgent",
                    role="You are a helpful and concise assistant.",
                    instructions=instructions,
                    tools=tools,
                    reasoning=desired_reasoning,
                    model_params={"temperature": 0.7},
                )

            # 4. Create Agent via Factory
            self.agent = await AgentFactory.create_agent(
                config, db=db, llm_model=self.llm_model
            )
            self._reasoning_enabled = desired_reasoning

            # 5. Inject Knowledge Tools (Function-based)
            if (
                kwargs.get("enable_knowledge", True)
                and HAS_KNOWLEDGE_TOOLS
                and self.agent
            ):
                knowledge_tools = [search_knowledge_base, query_knowledge_graph]
                # Avoid duplicates
                existing_names = [
                    t.name if hasattr(t, "name") else str(t) for t in self.agent.tools
                ]
                for kt in knowledge_tools:
                    if kt.__name__ not in existing_names:
                        self.agent.tools.append(kt)

                if "search_knowledge_base" not in str(self.agent.instructions):
                    self.agent.instructions.append(
                        "Use 'search_knowledge_base' to find information in the user's documents. "
                        "Use 'query_knowledge_graph' for complex queries involving relationships."
                    )

            # 6. Save State (Persistence)
            if session_id:
                try:
                    new_state = shared_state or SharedState(
                        session_id=session_id, mode="quick"
                    )
                    # We need to serialize AgentConfig to dict for SharedState
                    # SharedState.agent_config expects a Pydantic model or dict
                    # Assuming SharedState definition from previous search
                    # We update it
                    new_state.agent_config = config  # Pydantic model
                    await state_manager.save_state(session_id, new_state)
                except Exception as e:
                    logger.warning(
                        f"Failed to save shared state for session {session_id} (Redis down?): {e}"
                    )

        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            logger.error(f"Failed to create agent for QuickHandler: {e}\n{error_trace}")
            # Write to a temp file for debugging
            try:
                with open("quick_handler_error.log", "w") as f:
                    f.write(f"Error: {e}\nTraceback:\n{error_trace}")
            except Exception:
                pass
            self.agent = None

    async def _process_files(self, files: list, session_id: str) -> tuple[str, list]:
        """
        Process uploaded files:
        1. Extract text content for context injection (Small files).
        2. Save to Session KB for RAG (Large files).
        3. Handle Images for Multimodal support.

        Returns:
            (context_text, images_list)
        """
        from pathlib import Path
        from agno.media import Image

        context_parts = []
        images = []
        kb_manager = None

        # Ensure temp directory exists
        temp_dir = Path("data/temp") / session_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            filename = getattr(file, "filename", "unknown")
            file_ext = filename.split(".")[-1].lower() if "." in filename else ""

            try:
                # Save file to temp location first
                file_path = temp_dir / filename
                file_obj = file.file
                file_obj.seek(0)

                with open(file_path, "wb") as buffer:
                    import shutil

                    shutil.copyfileobj(file_obj, buffer)

                # 1. Image Handling
                if file_ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                    # Create Agno Image object
                    # Note: Local file paths need to be accessible
                    # Agno Image accepts 'filepath' or 'url'
                    # We use filepath
                    images.append(Image(filepath=str(file_path)))
                    context_parts.append(f"[Image: {filename}]")
                    continue

                # 2. Text/PDF Handling
                # Initialize KB Manager if needed
                if not kb_manager:
                    kb_manager = SessionKnowledgeManager(session_id)

                # Add to Knowledge Base (RAG)
                # This handles indexing in background usually, but here we do it sync for "Quick"
                if kb_manager.add_file(str(file_path)):
                    context_parts.append(
                        f"[Document added to Knowledge Base: {filename}]"
                    )
                else:
                    # Fallback to direct text extraction if KB fails or file small
                    file_obj.seek(0)
                    text_content = ""
                    if file_ext in [
                        "txt",
                        "md",
                        "json",
                        "py",
                        "js",
                        "html",
                        "css",
                        "csv",
                    ]:
                        content = file_obj.read()
                        if isinstance(content, bytes):
                            text_content = content.decode("utf-8", errors="ignore")
                        else:
                            text_content = str(content)
                    elif file_ext == "pdf":
                        try:
                            from pypdf import PdfReader

                            reader = PdfReader(file_obj)
                            for page in reader.pages:
                                text_content += page.extract_text() + "\n"
                        except ImportError:
                            text_content = "[Error: pypdf not installed]"

                    if text_content:
                        # Truncate
                        if len(text_content) > 5000:
                            text_content = (
                                text_content[:5000] + "\n...[Content truncated]..."
                            )
                        context_parts.append(
                            f"File: {filename}\nContent:\n{text_content}\n"
                        )

            except Exception as e:
                logger.error(f"Failed to process file {filename}: {e}")
                context_parts.append(f"File: {filename} (Error: {str(e)})")

        return "\n\n".join(context_parts), images

    async def process(
        self, input_text: str, intent: IntentResult, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        db = kwargs.get("db")
        session_id = kwargs.get("session_id")
        files = kwargs.get("files")

        # Pass kwargs to initialization to control features
        # Note: we pass session_id to enable SharedState persistence
        # Remove 'db' and 'session_id' from kwargs if they exist to avoid "multiple values" TypeError
        init_kwargs = kwargs.copy()
        if "db" in init_kwargs:
            del init_kwargs["db"]
        if "session_id" in init_kwargs:
            del init_kwargs["session_id"]

        await self._ensure_agent_initialized(db, session_id=session_id, **init_kwargs)

        if not self.agent:
            yield {
                "type": "error",
                "content": _("Agent not initialized for QuickHandler."),
            }
            return

        # Enhance instructions based on extracted Intent Entities (if available)
        # Assuming intent.task_params contains extraction results from NLU
        if intent and intent.task_params:
            entities = intent.task_params.get("entities") or []
            locations = intent.task_params.get("locations") or []
            time_range = intent.task_params.get("time_range")

            context_notes = []
            if entities:
                context_notes.append(f"Key Entities: {', '.join(entities)}")
            if locations:
                context_notes.append(f"Locations: {', '.join(locations)}")
            if time_range:
                context_notes.append(f"Time Range: {time_range}")

            if context_notes:
                # We inject these as system prompt augmentation for this turn
                # Or append to input_text
                # Appending to input is safer for "Quick" mode as it's immediate context
                entity_context = "\n[Detected Context]: " + " | ".join(context_notes)
                input_text += entity_context
                yield {
                    "type": "status",
                    "content": f"已识别关键信息: {', '.join(context_notes)}",
                }

        # Handle file uploads (In-memory RAG / Multimodal)
        images = []
        if files and session_id:
            file_names = [getattr(f, "filename", "unknown_file") for f in files]
            if file_names:
                yield {
                    "type": "status",
                    "content": f"正在处理文件: {', '.join(file_names)}...",
                }

                file_context, file_images = await self._process_files(files, session_id)

                # Update context
                if file_context:
                    input_text += f"\n\n[User Uploaded Files Context]\n{file_context}"

                # Update images
                if file_images:
                    images.extend(file_images)
                    yield {
                        "type": "status",
                        "content": f"已识别 {len(file_images)} 张图片。",
                    }

                # Attach Session KB if created
                kb_manager = SessionKnowledgeManager(session_id)
                kb = kb_manager.get_knowledge_base(
                    api_key=self.llm_model.api_key if self.llm_model else None,
                    base_url=self.llm_model.base_url if self.llm_model else None,
                )
                if kb:
                    # Dynamically attach KB to current agent instance
                    self.agent.knowledge = kb
                    self.agent.search_knowledge = True  # Enable search
                    # Ensure agent knows about the new capability
                    if "You have access to uploaded files" not in str(
                        self.agent.instructions
                    ):
                        self.agent.instructions.append(
                            "You have access to uploaded files in your knowledge base. Always search them if the user asks about file content."
                        )
                    yield {"type": "status", "content": "知识库已更新。"}

        try:
            # Load History
            history_messages = []
            if db and session_id:
                history = SessionHistory(db)
                # Get more messages to allow compression to work
                msgs = await history.get_messages(session_id, limit=20)

                raw_history = []
                for m in msgs:
                    raw_history.append({"role": m.role, "content": m.content})

                # Apply Context Compression
                compressor = ContextCompressor(model=self.llm_model)
                # Compress if history is long (e.g. > 3000 tokens)
                history_messages = await compressor.compress_context(
                    raw_history, max_tokens=3000
                )

                if len(history_messages) < len(raw_history):
                    yield {
                        "type": "status",
                        "content": "历史对话过长，已自动压缩上下文。",
                    }

            # Stream response
            # Pass images if available
            run_kwargs = {"messages": history_messages, "stream": True}
            if images:
                run_kwargs["images"] = images

            # response_stream = await self.agent.arun(input_text, **run_kwargs)
            # TypeError: object async_generator can't be used in 'await' expression
            # This means arun(stream=True) returns an async generator directly.

            async for chunk in self.agent.arun(input_text, **run_kwargs):
                # Check for tool calls or status updates if available in chunk
                # Note: Agno chunk structure depends on version, checking common attributes

                # If chunk represents a tool call start or execution
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    # Identify which tool is being called
                    tool_names = [
                        tc.function.name for tc in chunk.tool_calls if tc.function
                    ]
                    if tool_names:
                        yield {
                            "type": "status",
                            "content": f"正在使用工具: {', '.join(tool_names)}...",
                        }

                reasoning = getattr(chunk, "reasoning", None) or getattr(chunk, "reasoning_content", None)
                if reasoning:
                    yield {"type": "think", "content": reasoning}

                content = getattr(chunk, "content", None)
                if content:
                    yield {"type": "content", "content": content}
                elif isinstance(chunk, str):
                    yield {"type": "content", "content": chunk}

        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            logger.error(f"QuickHandler processing failed: {e}\n{error_trace}")
            try:
                with open("quick_handler_process_error.log", "w") as f:
                    f.write(f"Error: {e}\nTraceback:\n{error_trace}")
            except Exception:
                pass
            yield {
                "type": "error",
                "content": _("I'm having trouble thinking right now."),
            }
