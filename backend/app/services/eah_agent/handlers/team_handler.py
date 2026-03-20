"""
Team Handler:
Handles 'team' intent: Multi-agent collaboration.
核心功能：
1. 协调多个智能体（如研究代理、数据代理等）合作完成任务。
2. 支持异步操作，确保在高并发场景下的响应速度。
3. 提供基础的错误处理机制，避免系统崩溃。
"""
import logging
from typing import AsyncGenerator, Dict, Any, Optional, Tuple, List
from pathlib import Path
import shutil

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent
from agno.media import Image

from app.services.eah_agent.core.agent_base_handler import BaseHandler, StreamResponse
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.services.eah_agent.core.agent_factory import AgentFactory
from app.services.eah_agent.domain.config import AgentConfig, TeamConfig, ToolConfig
from app.core.i18n import _
from app.models.llm_model import LLMModel
from app.core.config import settings
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor
from app.services.eah_agent.utils.session_kb import SessionKnowledgeManager
from app.services.eah_agent.handlers.file_processors import FileProcessorFactory
from app.services.eah_agent.utils.agno_types import is_run_output

logger = logging.getLogger(__name__)

try:
    from agno.tools.e2b import E2BTools
    HAS_E2B = True
except ImportError:
    HAS_E2B = False

TEAM_AGENT_CONFIG = {
    "temperature": 0.3,
    "show_tool_calls": True,
    "history_limit": 30,
    "compression_threshold": 3000
}

class TeamHandler(BaseHandler):
    """
    Handles 'team' intent: Multi-agent collaboration.
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)
        self.team_agent: Optional[Agent] = None

    async def _process_files(self, files: list, session_id: str) -> tuple[str, list]:
        """
        Process uploaded files for multimodal support and context.
        """
        context_parts = []
        images = []
        kb_manager = None

        base_temp_dir = getattr(settings, "TEMP_DIR", "data/temp")
        temp_dir = Path(base_temp_dir) / session_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            filename = getattr(file, "filename", "unknown")
            file_ext = filename.split(".")[-1].lower() if "." in filename else ""

            try:
                file_path = temp_dir / filename
                file_obj = file.file
                file_obj.seek(0)

                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file_obj, buffer)
                file_obj.seek(0)

                if file_ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                    images.append(Image(filepath=str(file_path)))
                    context_parts.append(f"[Image: {filename}]")
                    continue

                if not kb_manager:
                    kb_manager = SessionKnowledgeManager(session_id)

                processor = FileProcessorFactory.get_processor(file_ext)
                if processor:
                    result = processor.process(file_path, file_obj, filename, kb_manager)
                    if result.get("image"):
                        images.append(result["image"])
                    if result.get("context"):
                        context_parts.append(result["context"])
                else:
                    logger.warning(f"No processor found for file extension: {file_ext}")
                    context_parts.append(f"File: {filename} (Unsupported format)")

            except Exception as e:
                logger.error(f"Failed to process file {filename}: {e}")
                context_parts.append(f"File: {filename} (Error: {str(e)})")

        return "\n\n".join(context_parts), images

    def _enrich_input_with_intent(self, input_text: str, intent: Optional[IntentResult]) -> str:
        if not intent or not intent.task_params:
            return input_text
            
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
            input_text += "\n[Detected Context]: " + " | ".join(context_notes)
            
        return input_text

    async def _prepare_context(self, session_id: str, files: Optional[list[Any]]) -> tuple[str, list[Any]]:
        """统一处理文件上传和知识库挂载逻辑。"""
        if not session_id:
            return "", []

        context_text = ""
        images = []

        if files:
            file_context, file_images = await self._process_files(files, session_id)
            if file_context:
                context_text += f"[User Uploaded Files Context]\n{file_context}"
            images.extend(file_images)

        try:
            kb_manager = SessionKnowledgeManager(session_id)
            kb = kb_manager.get_knowledge_base(
                api_key=self.llm_model.api_key if self.llm_model else None,
                base_url=self.llm_model.base_url if self.llm_model else None,
            )
            if kb and self.team_agent:
                self.team_agent.knowledge = kb
                self.team_agent.search_knowledge = True
                if "search_knowledge_base" not in str(self.team_agent.instructions):
                    self.team_agent.instructions.append("Use 'search_knowledge_base' to access user documents.")
                
                if self.team_agent.team:
                    for member in self.team_agent.team:
                        member.knowledge = kb
                        member.search_knowledge = True
                        if "search_knowledge_base" not in str(member.instructions):
                            member.instructions.append("Use 'search_knowledge_base' to access user documents.")
        except Exception as e:
            logger.error(f"Failed to attach KB to team: {e}")

        return context_text, images

    async def _get_history_messages(self, db: Optional[AsyncSession], session_id: Optional[str]) -> tuple[list[Dict], bool]:
        """获取并压缩历史消息。"""
        if not db or not session_id:
            return [], False
        
        try:
            history = SessionHistory(db)
            limit = TEAM_AGENT_CONFIG["history_limit"]
            threshold = TEAM_AGENT_CONFIG["compression_threshold"]

            msgs = await history.get_messages(session_id, limit=limit)
            raw_history = [{"role": m.role, "content": m.content} for m in msgs]

            compressor = ContextCompressor(model=self.llm_model)
            compressed = await compressor.compress_context(raw_history, max_tokens=threshold)
            
            return compressed, len(compressed) < len(raw_history)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return [], False

    async def _handle_chunk(self, chunk: Any) -> AsyncGenerator[StreamResponse, None]:
        """统一处理 Agno 的流式输出块。"""
        if is_run_output(chunk):
            try:
                run_output_dict = chunk.to_dict()
            except Exception:
                run_output_dict = {
                    "content": getattr(chunk, "content", None),
                    "tools": getattr(chunk, "tools", []),
                    "messages": [m.to_dict() if hasattr(m, "to_dict") else m for m in getattr(chunk, "messages", [])],
                    "reasoning_content": getattr(chunk, "reasoning_content", None),
                    "metrics": getattr(chunk, "metrics", None)
                }
            yield {"type": "run_output", "data": run_output_dict}
            if not getattr(self, "_emitted_final_output", False):
                final_text = run_output_dict.get("content")
                if not final_text:
                    messages = run_output_dict.get("messages") or []
                    assistant_parts = []
                    for m in messages:
                        if isinstance(m, dict) and m.get("role") == "assistant":
                            c = m.get("content")
                            if isinstance(c, str) and c.strip():
                                assistant_parts.append(c)
                    final_text = "\n".join(assistant_parts).strip() if assistant_parts else None

                if final_text:
                    yield {"type": "content", "content": final_text}
                yield {"type": "status", "content": _("Team execution completed.")}
                self._emitted_final_output = True
            return

        agent_name = getattr(chunk, "agent_name", None)
        if not agent_name and hasattr(chunk, "extra_data"):
            agent_name = chunk.extra_data.get("agent_name")
        
        if agent_name and agent_name != getattr(self, "_current_agent_name", None):
            self._current_agent_name = agent_name
            yield {"type": "agent_switch", "content": agent_name}
        
        if hasattr(chunk, "tool_calls") and chunk.tool_calls:
            tool_names = [tc.function.name for tc in chunk.tool_calls if tc.function]
            if tool_names:
                yield {"type": "status", "content": _("[{}] 正在使用工具: {}...").format(self._current_agent_name or 'Agent', ', '.join(tool_names))}

        reasoning = getattr(chunk, "reasoning", None) or getattr(chunk, "reasoning_content", None)
        if reasoning:
            yield {"type": "think", "content": reasoning}

        content = getattr(chunk, "content", None)
        if content:
            yield {"type": "content", "content": content}
        elif isinstance(chunk, str):
            yield {"type": "content", "content": chunk}

    async def _ensure_team_initialized(self, db: Optional[AsyncSession] = None, intent: Optional[IntentResult] = None):
        if self.team_agent:
            return

        try:
            members = []
            
            task_params = intent.task_params if intent else {}
            
            team_type = task_params.get("team_type", "dynamic")
            roles = task_params.get("roles", [])
            
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
                    ], 
                    reasoning=True,
                    model_params={"temperature": 0.3}
                )
                researcher_config.tools = [t for t in researcher_config.tools if t]
                members.append(researcher_config)

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
                        tools=[],
                        reasoning=True,
                        model_params={"temperature": 0.1}
                    )
                    members.append(coder_config)
                else:
                    logger.warning("Coding agent requested but E2B not configured. Skipping or falling back.")
            
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
                tools=[],
                reasoning=True,
                model_params={"temperature": 0.1}
            )
            
            team_config = TeamConfig(
                name="DynamicTeam",
                leader_agent=leader_config,
                members=members
            )
            
            self.team_agent = await AgentFactory.create_team(team_config, db=db)
            
            if self.team_agent and self.team_agent.team:
                for member in self.team_agent.team:
                    if member.name == "Developer" and HAS_E2B and settings.E2B_API_KEY:
                        try:
                            e2b_tool = E2BTools(api_key=settings.E2B_API_KEY)
                            member.tools.append(e2b_tool)
                        except Exception as e:
                            logger.error(f"Failed to inject E2B tool to Developer: {e}")

            if self.team_agent:
                self.team_agent.monitoring = True
            
        except Exception as e:
            logger.error(f"Failed to create team agent: {e}")
            self.team_agent = None

    async def process(
        self, input_text: str, intent: Optional[IntentResult] = None, **kwargs: Any
    ) -> AsyncGenerator[StreamResponse, None]:
        db = kwargs.get("db")
        session_id = kwargs.get("session_id")
        files = kwargs.get("files")
        
        await self._ensure_team_initialized(db, intent)
        
        if not self.team_agent:
            yield {"type": "error", "content": _("Team initialization failed.")}
            return

        input_text = self._enrich_input_with_intent(input_text, intent)

        try:
            images = []
            if session_id:
                if files:
                    file_names = [getattr(f, "filename", "unknown_file") for f in files]
                    yield {"type": "status", "content": _("正在处理文件: {}...").format(', '.join(file_names))}
                
                file_context, images = await self._prepare_context(session_id, files)
                
                if file_context:
                    input_text += f"\n\n{file_context}"
                
                if images:
                    yield {"type": "status", "content": _("已识别 {} 张图片。").format(len(images))}
                
                if "search_knowledge_base" in str(getattr(self.team_agent, "instructions", "")):
                    yield {"type": "status", "content": _("团队知识库已更新。")}

            history_messages, was_compressed = await self._get_history_messages(db, session_id)
            if was_compressed:
                yield {"type": "status", "content": _("历史对话过长，已自动压缩上下文。")}

            yield {"type": "status", "content": _("Team collaborating...")}
            
            run_kwargs = {"messages": history_messages, "stream": True, "yield_run_output": True}
            if images:
                run_kwargs["images"] = images
            
            self._current_agent_name = None
            self._emitted_final_output = False
            async for chunk in self.team_agent.arun(input_text, **run_kwargs):
                async for output in self._handle_chunk(chunk):
                    yield output
            
        except Exception as e:
            logger.error(f"TeamHandler processing failed: {e}", exc_info=True)
            yield {"type": "error", "content": _("Team execution failed. Attempting to recover...")}
