"""
Team Handler:
Handles 'team' intent: Multi-agent collaboration.
核心功能：
1. 协调多个智能体（如研究代理、数据代理等）合作完成任务。
2. 支持异步操作，确保在高并发场景下的响应速度。
3. 提供基础的错误处理机制，避免系统崩溃。
"""
import logging
import json
from typing import AsyncGenerator, Dict, Any, Optional, List
from pathlib import Path
import shutil

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent
from agno.media import Image

from app.services.eah_agent.core.base_handler import BaseHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.services.eah_agent.core.agent_factory import AgentFactory
from app.services.eah_agent.domain.config import AgentConfig, TeamConfig, ToolConfig
from app.core.i18n import _
from app.models.llm_model import LLMModel
from app.core.config import settings
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor
from app.services.eah_agent.utils.session_kb import SessionKnowledgeManager

logger = logging.getLogger(__name__)

# Try to import E2B tools
try:
    from agno.tools.e2b import E2BTools
    HAS_E2B = True
except ImportError:
    HAS_E2B = False

class TeamHandler(BaseHandler):
    """
    Handles 'team' intent: Multi-agent collaboration.
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)
        self.team_agent: Optional[Agent] = None

    async def _process_files(self, files: list, session_id: str) -> tuple[str, list]:
        """
        Process uploaded files (Reuse logic from QuickHandler):
        1. Extract text content for context injection (Small files).
        2. Save to Session KB for RAG (Large files).
        3. Handle Images for Multimodal support.

        Returns:
            (context_text, images_list)
        """
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
                    shutil.copyfileobj(file_obj, buffer)

                # 1. Image Handling
                if file_ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                    images.append(Image(filepath=str(file_path)))
                    context_parts.append(f"[Image: {filename}]")
                    continue

                # 2. Text/PDF Handling
                # Initialize KB Manager if needed
                if not kb_manager:
                    kb_manager = SessionKnowledgeManager(session_id)

                # Add to Knowledge Base (RAG)
                if kb_manager.add_file(str(file_path)):
                    context_parts.append(
                        f"[Document added to Knowledge Base: {filename}]"
                    )
                else:
                    # Fallback to direct text extraction if KB fails or file small
                    file_obj.seek(0)
                    text_content = ""
                    if file_ext in ["txt", "md", "json", "py", "js", "html", "css", "csv"]:
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

    async def _ensure_team_initialized(self, db: Optional[AsyncSession] = None, intent: Optional[IntentResult] = None):
        """
        Dynamically initialize team based on intent.
        """
        # If already initialized, we might want to re-evaluate if the team structure needs to change based on new intent.
        # For simplicity, we keep the existing team if it exists, unless explicitly requested to change (not implemented here).
        if self.team_agent:
            return

        try:
            # Default members
            members = []
            
            # Analyze intent to determine team composition
            task_params = intent.task_params if intent else {}
            input_text_lower = "" # We don't have raw input here easily unless passed, but we rely on intent params
            
            # Use intent.intent or task_params to guide
            # Example: intent="team", task_params={"team_type": "research"}
            
            team_type = task_params.get("team_type", "dynamic")
            roles = task_params.get("roles", [])
            
            # 1. Researcher Agent (if needed)
            # If explicit "research" type or "researcher" role, or implied by task
            if team_type == "research" or "researcher" in roles or "research" in str(task_params):
                researcher_config = AgentConfig(
                    name="Researcher",
                    role="Research Specialist",
                    instructions=[
                        "Search for information using available tools.", 
                        "Verify facts and provide sources.",
                        "Be thorough and objective."
                    ],
                    tools=[
                        ToolConfig(name="duckduckgo", enabled=True, config={}),
                        # Add Tavily if available
                        # ToolConfig(name="tavily", enabled=True, config={"api_key": settings.TAVILY_API_KEY}) if settings.TAVILY_API_KEY else None
                    ], 
                    reasoning=True,
                    model_params={"temperature": 0.3}
                )
                # Filter None tools
                researcher_config.tools = [t for t in researcher_config.tools if t]
                members.append(researcher_config)

            # 2. Coding/Data Agent (if needed)
            if team_type == "coding" or "developer" in roles or "code" in str(task_params) or "data" in str(task_params):
                if HAS_E2B and settings.E2B_API_KEY:
                    coder_config = AgentConfig(
                        name="Developer",
                        role="Senior Developer",
                        instructions=[
                            "Write and execute code to solve problems.",
                            "Always use the E2B sandbox for code execution.",
                            "Analyze data using Python (pandas, numpy, etc.)."
                        ],
                        tools=[
                             # E2B tool will be added by Factory or here manually? 
                             # Factory currently supports 'e2b' if we add it to ToolFactory or handle it specially.
                             # Since E2B is a special case, we might need to handle it in Factory or use a custom ToolConfig.
                             # For now, let's assume we can add it via a custom tool config name "e2b_interpreter" if Factory supports it,
                             # OR we rely on the fact that we can't easily pass E2B object in Config JSON.
                             # We will inject E2B tool instance AFTER creation if Factory doesn't support it directly by name.
                             # Let's try to add a placeholder config and handle it in Factory or post-creation.
                        ],
                        reasoning=True,
                        model_params={"temperature": 0.1}
                    )
                    members.append(coder_config)
                else:
                    logger.warning("Coding agent requested but E2B not configured. Skipping or falling back.")
                    # Fallback to local python? Requirement says "MUST force E2BTools". So we skip.
            
            # 3. Writer/Editor (Always useful)
            writer_config = AgentConfig(
                name="Writer",
                role="Content Writer",
                instructions=[
                    "Write engaging content based on research or code outputs.", 
                    "Format with Markdown.",
                    "Ensure clarity and flow."
                ],
                tools=[],
                reasoning=False,
                model_params={"temperature": 0.7}
            )
            members.append(writer_config)
            
            # 4. Leader Agent
            leader_config = AgentConfig(
                name="TeamLeader",
                role="Team Coordinator",
                instructions=[
                    "You are the leader of this team.",
                    "Coordinate the team members to answer the user's request.",
                    "Break down complex tasks and assign them to the appropriate member.",
                    "Review outputs and synthesize the final answer.",
                    "If a member fails, try to rephrase the instruction or assign to another member."
                ],
                tools=[], # Leader usually doesn't need tools, just delegates
                reasoning=True, # Leader needs reasoning to plan
                model_params={"temperature": 0.1}
            )
            
            # Create Team Config
            team_config = TeamConfig(
                name="DynamicTeam",
                leader_agent=leader_config,
                members=members
            )
            
            self.team_agent = await AgentFactory.create_team(team_config, db=db)
            
            # Post-creation: Inject E2B tools if needed (since Config might not support object instances directly)
            # We iterate through created members to find "Developer" and add E2B tool
            if self.team_agent and self.team_agent.team:
                for member in self.team_agent.team:
                    if member.name == "Developer" and HAS_E2B and settings.E2B_API_KEY:
                        try:
                            e2b_tool = E2BTools(api_key=settings.E2B_API_KEY)
                            member.tools.append(e2b_tool)
                        except Exception as e:
                            logger.error(f"Failed to inject E2B tool to Developer: {e}")

            # 开启监控
            if self.team_agent:
                self.team_agent.monitoring = True
            
        except Exception as e:
            logger.error(f"Failed to create team agent: {e}")
            self.team_agent = None

    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        db = kwargs.get("db")
        session_id = kwargs.get("session_id")
        files = kwargs.get("files")
        
        # 1. Initialize Team
        await self._ensure_team_initialized(db, intent)
        
        if not self.team_agent:
             yield {"type": "error", "content": _("Team initialization failed.")}
             return

        try:
            # 2. Handle File Uploads (Multimodal & RAG)
            images = []
            if files and session_id:
                file_names = [getattr(f, "filename", "unknown_file") for f in files]
                yield {"type": "status", "content": f"正在处理文件: {', '.join(file_names)}..."}
                
                file_context, file_images = await self._process_files(files, session_id)
                
                if file_context:
                    input_text += f"\n\n[User Uploaded Files Context]\n{file_context}"
                
                if file_images:
                    images.extend(file_images)
                    yield {"type": "status", "content": f"已识别 {len(file_images)} 张图片。"}
                
                # Update Shared Knowledge Base
                kb_manager = SessionKnowledgeManager(session_id)
                kb = kb_manager.get_knowledge_base(
                    api_key=self.llm_model.api_key if self.llm_model else None,
                    base_url=self.llm_model.base_url if self.llm_model else None,
                )
                
                if kb:
                    # Inject KB to Leader and All Members
                    # Leader
                    self.team_agent.knowledge = kb
                    self.team_agent.search_knowledge = True
                    if "search_knowledge_base" not in str(self.team_agent.instructions):
                        self.team_agent.instructions.append("Use 'search_knowledge_base' to access user documents.")
                    
                    # Members
                    if self.team_agent.team:
                        for member in self.team_agent.team:
                            member.knowledge = kb
                            member.search_knowledge = True
                            if "search_knowledge_base" not in str(member.instructions):
                                member.instructions.append("Use 'search_knowledge_base' to access user documents.")
                    
                    yield {"type": "status", "content": "团队知识库已更新。"}

            # 3. Context Compression
            history_messages = []
            if db and session_id:
                history = SessionHistory(db)
                msgs = await history.get_messages(session_id, limit=30) # Get more for team context
                
                raw_history = [{"role": m.role, "content": m.content} for m in msgs]
                
                compressor = ContextCompressor(model=self.llm_model)
                history_messages = await compressor.compress_context(raw_history, max_tokens=3000)
                
                if len(history_messages) < len(raw_history):
                    yield {"type": "status", "content": "历史对话已压缩，优化团队协作效率。"}

            yield {"type": "status", "content": _("Team collaborating...")}
            
            # 4. Async Streaming Execution
            # Prepare arguments
            run_kwargs = {"messages": history_messages, "stream": True}
            if images:
                run_kwargs["images"] = images
            
            # Execute
            # Check if it's an async generator (it should be if stream=True and using async model/client)
            # Agno's run() might be synchronous or return a sync generator even if async is possible?
            # Wait, the user requirement says: `await self.team_agent.arun(..., stream=True)`
            # So I MUST use `arun`.
            
            response_stream = await self.team_agent.arun(input_text, **run_kwargs)
            
            current_agent_name = None
            
            async for chunk in response_stream:
                # 5. Intercept Agent Switch
                # Check for agent name in chunk (depends on Agno version/implementation)
                # Often it's in `extra_data` or a specific attribute
                agent_name = getattr(chunk, "agent_name", None)
                if not agent_name and hasattr(chunk, "extra_data"):
                     agent_name = chunk.extra_data.get("agent_name")
                
                if agent_name and agent_name != current_agent_name:
                    current_agent_name = agent_name
                    yield {"type": "agent_switch", "content": agent_name}
                
                # 6. Intercept Tool Calls
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    tool_names = [tc.function.name for tc in chunk.tool_calls if tc.function]
                    if tool_names:
                        yield {"type": "status", "content": f"[{current_agent_name or 'Agent'}] 正在使用工具: {', '.join(tool_names)}..."}

                # 7. Yield Reasoning/Think
                reasoning = getattr(chunk, "reasoning", None) or getattr(chunk, "reasoning_content", None)
                if reasoning:
                    yield {"type": "think", "content": reasoning}

                # 8. Yield Content
                content = getattr(chunk, 'content', None)
                if content:
                     yield {"type": "content", "content": content}
                elif isinstance(chunk, str):
                     yield {"type": "content", "content": chunk}
            
        except Exception as e:
            logger.error(f"TeamHandler processing failed: {e}", exc_info=True)
            yield {"type": "error", "content": _("Team execution failed. Attempting to recover...")}
            # Robustness: In a real scenario, we might retry with a simpler agent or different strategy here.
