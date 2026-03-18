"""
自规划 Agent 任务分发 (带 Chain-of-Thought)
Agno的Agent类有专门的参数reasoning = True/False，默认False。
如果设置为True，Agno会在执行任务时，返回任务的执行计划（Chain-of-Thought）。
核心功能：
1. 解析用户定义的任务（如报告生成、数据处理等）。
2. 执行任务中的每个步骤，支持异步操作。
3. 提供执行状态反馈（如“正在执行步骤 1”等）。
4. 处理异常情况，确保任务的稳定性。
"""
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
from app.services.eah_agent.core.base_handler import BaseHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.services.eah_agent.core.agent_factory import AgentFactory
from app.services.eah_agent.domain.config import AgentConfig, ToolConfig
from app.core.i18n import _
from app.models.llm_model import LLMModel
from app.models.agent_plan import AgentPlan, AgentTask, PlanStatus, TaskStatus
from agno.agent import Agent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import json
import os
from app.services.eah_agent.skills.manager import Skills
from app.services.eah_agent.skills.loaders.local import LocalSkills
from app.services.eah_agent.tools.factory import get_mcp_toolkit
from agno.tools import Toolkit
from agno.tools.e2b import E2BTools
from app.core.shared_state import StateManager, SharedState
from app.services.eah_agent.utils.session_kb import SessionKnowledgeManager
from app.core.context_compressor import ContextCompressor
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.config import settings

logger = logging.getLogger(__name__)

class PlanHandler(BaseHandler):
    """
    Handles 'task' intent with autonomous planning (ReAct).
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)
        self.agent: Optional[Agent] = None
        # Agent initialization is deferred to the first process call

    def _get_workspace_dir(self) -> str:
        """获取用于文件操作的工作区目录。"""
        if hasattr(settings, "WORKSPACE_DIR") and settings.WORKSPACE_DIR:
            return settings.WORKSPACE_DIR
        
        # 默认为 backend/workspace
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        workspace = os.path.join(base_dir, "workspace")
        os.makedirs(workspace, exist_ok=True)
        return workspace

    async def _load_mcp_tools(self) -> List[Toolkit]:
        """
        从配置中加载 MCP 工具。
        """
        mcp_tools = []
        # 检查 settings 中的 MCP_SERVERS 配置（字典列表）
        if hasattr(settings, "MCP_SERVERS") and settings.MCP_SERVERS:
             for server_config in settings.MCP_SERVERS:
                 try:
                     toolkit = await get_mcp_toolkit(server_config)
                     mcp_tools.append(toolkit)
                 except Exception as e:
                     logger.error(f"Failed to load MCP tool {server_config}: {e}")
        return mcp_tools

    async def _load_skills(self) -> tuple[List[Any], str]:
        """
        从本地文件系统加载技能。
        返回 (tools, system_prompt_snippet) 元组。
        """
        skill_tools = []
        skill_prompt = ""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            skills_dir = os.path.join(base_dir, "skills")
            
            # 如果存在 'skills' 目录但没有 SKILL.md，也检查子目录
            if os.path.exists(skills_dir):
                loader = LocalSkills(skills_dir, validate=False) # 禁用验证以提高健壮性
                manager = Skills([loader])
                
                skill_tools.extend(manager.get_tools())
                skill_prompt = manager.get_system_prompt_snippet()
        except Exception as e:
            logger.error(f"Failed to load skills: {e}")
        
        return skill_tools, skill_prompt

    async def _ensure_agent_initialized(self, session_id: str = None):
        """
        Lazily initialize the agent using AgentFactory.
        """
        if not self.agent and self.llm_model:
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
                
                # 2. Use existing config if available (State Restoration)
                config = None
                if shared_state and shared_state.agent_config:
                    # In a real scenario, we might want to reload this config
                    # But for PlanHandler, we usually re-construct it to ensure tool freshness
                    # For now, we proceed to create fresh config but could use shared_state for history/memory
                    pass

                # Create a default config for PlanHandler
                workspace_dir = self._get_workspace_dir()
                
                # 配置 Solo 模式的工具
                tools_config = [
                    ToolConfig(name="duckduckgo", enabled=True, config={}),
                    # 替换本地 Python 工具为 E2B 沙箱工具
                    # ToolConfig(name="python", enabled=True, config={"run_code": True, "pip_install": True}),
                    ToolConfig(name="file_tools", enabled=True, config={"base_dir": workspace_dir}),
                    ToolConfig(name="plan_tools", enabled=True, config={})
                ]

                # 显式初始化 E2B 工具
                e2b_tools = []
                if settings.E2B_API_KEY:
                    try:
                        e2b_tool = E2BTools(
                            api_key=settings.E2B_API_KEY,
                            # 确保沙箱工作目录与现有逻辑一致 (如果 E2B 支持此配置，否则它使用自己的沙箱环境)
                            # E2B 通常是隔离环境，我们可能不需要映射本地路径，或者只能上传文件
                        )
                        e2b_tools.append(e2b_tool)
                    except Exception as e:
                        logger.error(f"Failed to initialize E2B tools: {e}")

                # 加载 MCP 工具
                mcp_toolkits = await self._load_mcp_tools()
                
                # 加载技能
                skill_tools, skill_prompt = await self._load_skills()
                
                instructions = [
                    "You are an autonomous planning agent with advanced task decomposition capabilities.",
                    "Your goal is to solve the user's request by creating a dependency-aware plan and executing it.",
                    "1. FIRST, analyze the request deeply. If the task is complex, break it down into atomic subtasks.",
                    "   - Use `update_plan` to create the initial plan.",
                    "   - Define `dependencies` for each step to ensure correct execution order.",
                    "   - Set `task_type` (e.g., search, code, file) for clarity.",
                    "2. THEN, execute the steps respecting the dependencies.",
                    "   - A step can only start if its dependencies are 'completed'.",
                    "   - Before starting a step, mark it as 'running'.",
                    "   - Use available tools (Search, Python, File) to complete the step.",
                    "   - After completing a step, mark it as 'completed'.",
                    "3. DYNAMICALLY ADAPT: If a step fails or new information emerges, modify the plan (add/remove steps).",
                    "4. Provide a final summary of the results."
                ]
                
                if skill_prompt:
                    instructions.append(skill_prompt)

                config = AgentConfig(
                    name="PlanAgent",
                    role="Autonomous Planner",
                    instructions=instructions,
                    tools=tools_config,
                    reasoning=True,
                    model_params={"temperature": 0.1} # Lower temp for planning
                )
                
                self.agent = await AgentFactory.create_agent(config, llm_model=self.llm_model)
                
                # 开启监控
                if self.agent:
                    self.agent.monitoring = True

                # 直接注入 MCP、技能和 E2B 工具
                if self.agent:
                    if mcp_toolkits:
                        self.agent.tools.extend(mcp_toolkits)
                    if skill_tools:
                        self.agent.tools.extend(skill_tools)
                    if e2b_tools:
                        self.agent.tools.extend(e2b_tools)

                # Save State (Persistence)
                if session_id:
                    try:
                        new_state = shared_state or SharedState(
                            session_id=session_id, mode="plan"
                        )
                        new_state.agent_config = config
                        await state_manager.save_state(session_id, new_state)
                    except Exception as e:
                        logger.warning(
                            f"Failed to save shared state for session {session_id} (Redis down?): {e}"
                        )
                        
            except Exception as e:
                logger.error(f"Failed to create agent for PlanHandler: {e}")
                self.agent = None

    async def _persist_plan(self, db: AsyncSession, session_id: str, steps: List[Dict]):
        """
        将计划和任务持久化到数据库。
        """
        if not db or not session_id:
            return
            
        try:
            # 检查是否存在活跃的计划
            stmt = select(AgentPlan).filter(
                AgentPlan.session_id == session_id,
                AgentPlan.status.in_([PlanStatus.PLANNING, PlanStatus.RUNNING])
            ).order_by(AgentPlan.created_at.desc())
            
            result = await db.execute(stmt)
            plan = result.scalars().first()
            
            if not plan:
                # 如果不存在则创建新计划
                # 注意：此处不易获取 user_goal，使用通用占位符
                plan = AgentPlan(
                    session_id=session_id,
                    user_goal="Plan Execution", 
                    status=PlanStatus.RUNNING
                )
                db.add(plan)
                await db.flush()
            
            # 由于 update_plan 提供完整列表，此处同步数据库状态。
            # 为简化起见，先清除旧任务再重新插入。
            await db.execute(delete(AgentTask).where(AgentTask.plan_id == plan.id))
            
            new_tasks = []
            for i, step in enumerate(steps):
                status_str = step.get("status", "pending").upper()
                # 安全地将字符串状态映射为枚举
                status_enum = TaskStatus.PENDING
                if status_str == "RUNNING":
                    status_enum = TaskStatus.IN_PROGRESS
                elif status_str == "COMPLETED":
                    status_enum = TaskStatus.COMPLETED
                elif status_str == "FAILED":
                    status_enum = TaskStatus.FAILED
                
                # 使用元数据或上下文作为任务类型和依赖项
                input_context = {}
                if "dependencies" in step:
                    input_context["dependencies"] = step["dependencies"]
                if "task_type" in step:
                    input_context["task_type"] = step["task_type"]

                task = AgentTask(
                    plan_id=plan.id,
                    sequence=i+1,
                    name=step.get("title", f"Step {i+1}"),
                    description=step.get("description", ""),
                    status=status_enum,
                    assigned_agent_role="executor",
                    input_context=input_context,
                    dependencies=step.get("dependencies", [])
                )
                new_tasks.append(task)
            
            db.add_all(new_tasks)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to persist plan: {e}")

    async def _process_files(self, files: list, session_id: str) -> tuple[str, list]:
        """
        Process uploaded files for multimodal support and context.
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
                    images.append(Image(filepath=str(file_path)))
                    context_parts.append(f"[Image: {filename}]")
                    continue

                # 2. Text/PDF Handling
                if not kb_manager:
                    kb_manager = SessionKnowledgeManager(session_id)

                if kb_manager.add_file(str(file_path)):
                    context_parts.append(f"[Document added to Knowledge Base: {filename}]")
                else:
                    context_parts.append(f"[File saved: {filename}]")

            except Exception as e:
                logger.error(f"Failed to process file {filename}: {e}")
                context_parts.append(f"File: {filename} (Error: {str(e)})")

        return "\n\n".join(context_parts), images

    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        yield {"type": "status", "content": _("Initializing PlanAgent...")}
        
        db: Optional[AsyncSession] = kwargs.get("db")
        session_id: Optional[str] = kwargs.get("session_id")
        files = kwargs.get("files")
        
        await self._ensure_agent_initialized(session_id=session_id)

        if not self.agent:
             yield {"type": "error", "content": _("Agent not initialized for PlanHandler.")}
             return

        # Handle file uploads (In-memory RAG / Multimodal)
        images = []
        if files and session_id:
            file_names = [getattr(f, "filename", "unknown_file") for f in files]
            if file_names:
                yield {
                    "type": "status",
                    "content": f"Processing files: {', '.join(file_names)}...",
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
                        "content": f"Identified {len(file_images)} images.",
                    }

                # Attach Session KB if created
                try:
                    kb_manager = SessionKnowledgeManager(session_id)
                    kb = kb_manager.get_knowledge_base(
                        api_key=self.llm_model.api_key if self.llm_model else None,
                        base_url=self.llm_model.base_url if self.llm_model else None,
                    )
                    if kb:
                        self.agent.knowledge = kb
                        self.agent.search_knowledge = True
                        if "search_knowledge_base" not in str(self.agent.instructions):
                             self.agent.instructions.append(
                                "Use 'search_knowledge_base' to find information in the user's documents. "
                            )
                        yield {"type": "status", "content": "Knowledge base updated."}
                except Exception as e:
                    logger.error(f"Failed to load session knowledge base: {e}")

        try:
            yield {"type": "status", "content": _("Analyzing task and creating plan...")}
            
            # Context Compression
            if db and session_id:
                try:
                    history = SessionHistory(db)
                    msgs = await history.get_messages(session_id, limit=20)
                    raw_history = [{"role": m.role, "content": m.content} for m in msgs]
                    
                    compressor = ContextCompressor(model=self.llm_model)
                    history_messages = await compressor.compress_context(raw_history, max_tokens=3000)
                    
                    if len(history_messages) < len(raw_history):
                        yield {"type": "status", "content": "Context compressed."}
                except Exception as e:
                    logger.warning(f"Context compression failed: {e}")
            
            # We add a specific instruction to the user prompt to enforce the dependency-aware behavior
            enhanced_prompt = f"""
            Task: {input_text}
            
            Remember to:
            1. Break this down into steps with clear dependencies.
            2. Execute steps in order. 
            3. Update the plan status frequently.
            """
            
            # Execute the agent with streaming (Async)
            run_kwargs = {"stream": True, "yield_run_output": True}
            if images:
                run_kwargs["images"] = images
                
            response_stream = await self.agent.arun(enhanced_prompt, **run_kwargs)
            
            async for chunk in response_stream:
                # 提取最终 RunOutput 对象
                if type(chunk).__name__ == "RunOutput":
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
                    yield {
                        "type": "run_output",
                        "data": run_output_dict
                    }
                    continue

                # 1. Tool Status
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    tool_names = [tc.function.name for tc in chunk.tool_calls if tc.function]
                    if tool_names:
                        yield {"type": "status", "content": f"正在使用工具: {', '.join(tool_names)}..."}
                        
                        # Plan Interception logic inside loop
                        for tc in chunk.tool_calls:
                            if tc.function and tc.function.name == "update_plan":
                                try:
                                    args = json.loads(tc.function.arguments)
                                    steps = args.get("steps", [])
                                    yield {"type": "plan_step", "content": steps}
                                    if db and session_id:
                                        await self._persist_plan(db, session_id, steps)
                                except Exception as e:
                                    logger.error(f"Failed to process update_plan: {e}")
                            
                            # File Interception
                            if tc.function and tc.function.name in ["save_file", "write_file"]:
                                try:
                                    args = json.loads(tc.function.arguments)
                                    file_path = args.get("file_path") or args.get("path")
                                    if file_path:
                                        import os
                                        file_name = os.path.basename(file_path)
                                        yield {
                                            "type": "file", 
                                            "content": {"name": file_name, "path": file_path, "size": 0, "type": "generated"}
                                        }
                                except Exception: 
                                    pass

                # 2. Reasoning
                reasoning = getattr(chunk, "reasoning", None) or getattr(chunk, "reasoning_content", None)
                if reasoning:
                    yield {"type": "think", "content": reasoning}

                # 3. Content
                content = getattr(chunk, "content", None)
                if content:
                    yield {"type": "content", "content": content}
                elif isinstance(chunk, str):
                    yield {"type": "content", "content": chunk}

        except Exception as e:
            logger.error(f"PlanHandler processing failed: {e}")
            yield {"type": "error", "content": _("I encountered an error while planning.")}
