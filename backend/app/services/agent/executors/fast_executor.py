import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.models.llm_model import LLMModel
from app.services.agent.schemas.intent import IntentResult
from app.services.agent.executors.base.light_base_executor import LightBaseExecutor
from app.services.agent.components.memory_manager import DefaultMemoryManager
from app.services.agent.orchestration.builder import AgentAssembler
from app.services.agent.utils.stream_adapter import AgnoStreamAdapter
from app.services.agent.document.file_orchestrator import FileOrchestrator

logger = logging.getLogger("eah.executors.fast")

class FastExecutor(LightBaseExecutor):
    """
    极速 QA 执行器
    旁路重型规划与反思，采用并发上下文组装，以 O(1) 拓扑实现极低延迟。
    """

    SYSTEM_INSTRUCTIONS: List[str] = [
        "You are a helpful assistant operating in Fast mode — fast, accurate, and concise.",
        "When using web search or tools, always cite sources inline as [1], [2], … "
        "and append a **References** section at the end of your answer.",
        "If a tool call fails or times out, acknowledge it honestly and answer "
        "from your existing knowledge instead of fabricating results.",
        "Keep answers focused; avoid unnecessary verbosity.",
        "CRITICAL: In this mode, you DO NOT have tools to create, write, or export files (like .docx, .pdf, etc.). If the user asks you to generate a file, you MUST explicitly inform them that you can only provide the text content in the chat, and they need to switch to 'Task' mode for file generation.",
        "Always reply in the same language the user used.",
    ]

    def __init__(self, llm_model: Optional[LLMModel] = None, memory_manager: Optional[DefaultMemoryManager] = None):
        super().__init__(llm_model=llm_model, memory_manager=memory_manager)
        self.stream_adapter = AgnoStreamAdapter()

    async def execute(
        self, 
        input_text: str, 
        intent: Optional[IntentResult] = None, 
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        db: AsyncSession = kwargs.get("db")
        session_id: str = kwargs.get("session_id")
        files: List[Any] = kwargs.get("files", [])
        
        setup_tasks = [
            self._prepare_agent(db, session_id, kwargs, intent),
            self._prepare_history(session_id, current_query=input_text),
            self._handle_incoming_files(session_id, files)
        ]
        
        results = await asyncio.gather(*setup_tasks, return_exceptions=True)
        
        # 结果解析与降级处理
        agent = results[0] if not isinstance(results[0], Exception) else None
        if not agent:
            error_msg = str(results[0]) if isinstance(results[0], Exception) else "Unknown"
            logger.error(f"Agent assembly failed: {error_msg}")
            yield {"type": "error", "content": "Agent assembly failed"}
            return

        history_msgs = results[1] if not isinstance(results[1], Exception) else []
        if isinstance(results[1], Exception):
            logger.warning(f"History retrieval degraded gracefully: {results[1]}")

        file_result = results[2]
        if isinstance(file_result, Exception):
            logger.warning(f"File handling degraded gracefully: {file_result}")
            file_ctx, media_objs, kb = "", [], None
        else:
            file_ctx, media_objs, kb = file_result

        # 2. Instruction Orchestration
        base_instructions = getattr(agent, "instructions", None)
        instructions = list(self.SYSTEM_INSTRUCTIONS)
        
        if isinstance(base_instructions, str):
            if base_instructions.strip():
                instructions.append(base_instructions)
        elif isinstance(base_instructions, list):
            instructions.extend([str(x) for x in base_instructions if str(x).strip()])
            
        if kb:
            # Ephemeral RAG: Mount session knowledge base instead of violent text concatenation
            agent.knowledge = kb
            # Enable the knowledge search tool for the agent
            if agent.tools is None:
                agent.tools = []
            
            # Ensure the agent has the search_knowledge_base tool
            has_kb_tool = any(getattr(t, "__name__", "") == "search_knowledge_base" for t in agent.tools)
            if not has_kb_tool:
                agent.search_knowledge = True # Agno standard way to enable knowledge search
                
            yield {"type": "status", "content": f"已将 {len(files)} 个文件挂载至临时向量知识库。"}
        elif file_ctx:
            # Fallback for very small contexts or when KB initialization fails
            instructions.append(f"Uploaded Files Context:\n{file_ctx}")
            yield {"type": "status", "content": f"已处理 {len(files)} 个文件。"}

        # 3. Contextual Augmentation
        augmented_input = self._augment_input(input_text, intent)

        # [P10 Determinism] Quick 模式物理隔离：由 NLU 路由决定工具挂载，去除一刀切硬编码
        is_quick_mode = intent and intent.intent == "quick"
        if is_quick_mode:
            instructions.append("CRITICAL: You are in QUICK mode. Answer directly and concisely. Prioritize retrieving information from the attached Knowledge Base.")
            # Note: We NO LONGER clear agent.tools here. Tools are resolved via Strategy Pattern in Intent Router.

        # 4. Streaming Execution
        try:
            async for chunk in agent.arun(
                augmented_input,
                messages=history_msgs,
                images=media_objs,
                instructions=instructions,
                stream=True,
                stream_events=True
            ):
                async for event in self.stream_adapter.to_standard_events(chunk):
                    yield event
            
            async for event in self.stream_adapter.flush():
                yield event

        except Exception as e:
            logger.error(f"FastExecutor execution failed: {e}", exc_info=True)
            yield self._yield_error("Internal processing error", e)

    async def _prepare_agent(self, db: AsyncSession, session_id: str, kwargs: Any, intent: Optional[IntentResult] = None) -> Agent:
        """[Dependency Injection] 动态挂载 Agent 配置。"""
        agent_id = kwargs.get("agent_id")
        reasoning = kwargs.get("enable_reasoning", False)
        search = kwargs.get("enable_search", True)
        user_id = kwargs.get("user_id", "default_user")

        #利用 Agno 原生能力处理跨会话用户偏好记忆
        from app.core.config import settings
        agno_storage = None
        try:
            # 引入 Agno 原生的 PostgresDb (用于长期状态和记忆)
            from agno.db.postgres import AsyncPostgresDb
            db_url = str(settings.DATABASE_URL)
            if db_url:
                agno_storage = AsyncPostgresDb(
                    db_url=db_url,
                    session_table="agno_sessions",
                    memory_table="agno_user_memories"
                )
        except Exception as e:
            logger.warning(f"Failed to initialize Agno native storage: {e}")

        assembler = AgentAssembler(db, agent_id)
        return await assembler.build(
            session_id=session_id,
            reasoning_override=reasoning,
            enable_search=search,
            intent=intent,
            storage=agno_storage,
            user_id=user_id,
            enable_user_memories=True if agno_storage else False,
            add_memories_to_context=True if agno_storage else False,
        )

    async def _handle_incoming_files(self, session_id: str, files: List[Any]) -> Tuple[str, List[Any], Optional[Any]]:
        """[Performance] 并发解析文件，消除串行 I/O 耗时瓶颈。构建临时知识库 (Ephemeral RAG)。"""
        if not files:
            return "", [], None

        # Initialize Ephemeral Knowledge Base
        from app.services.agent.utils.session_kb import SessionKnowledgeManager
        kb_manager = SessionKnowledgeManager(session_id=session_id)
        kb = kb_manager.get_knowledge_base()

        tasks = [
            FileOrchestrator.process_file(f.file, f.filename, session_id=session_id, kb_manager=kb_manager if kb else None)
            for f in files
        ]
        results = await asyncio.gather(*tasks)
        
        contexts = []
        media = []
        
        kb_loaded = False

        for r in results:
            if r["status"] == "success":
                # Text content is added to KB by processors if kb_manager is provided.
                # If kb is successfully initialized and text content exists, consider it loaded.
                if kb and r.get("content_text") and r.get("file_type") in ("text", "pdf"):
                    kb_loaded = True
                
                # We still collect text for fallback or if KB failed
                if r.get("content_text"):
                    contexts.append(r["content_text"])
                if r.get("media_objects"):
                    media.extend(r["media_objects"])
        
        # If KB is successfully loaded, we don't need to return the giant string context to pollute the prompt
        # But we still return media for visual models
        if kb_loaded:
            return "", media, kb
            
        return "\n\n".join(contexts), media, None

    def _augment_input(self, text: str, intent: Optional[IntentResult]) -> str:
        """[NLU Augmentation] 将意图参数注入 Prompt，物理限制 LLM 的推理上下文边界。"""
        if not intent or not intent.parameters:
            return text
        
        params = intent.parameters
        notes = []
        if "entities" in params:
            notes.append(f"Entities: {params['entities']}")
        if "time" in params:
            notes.append(f"Time Context: {params['time']}")
        
        if notes:
            return f"[Context: {' | '.join(notes)}]\n{text}"
        return text
