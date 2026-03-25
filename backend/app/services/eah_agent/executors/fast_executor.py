import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.models.llm_model import LLMModel
from app.services.eah_agent.schemas.intent import IntentResult
from app.services.eah_agent.executors.light_base_executor import LightBaseExecutor
from app.services.eah_agent.components.memory_manager import DefaultMemoryManager
from app.services.eah_agent.orchestration.builder import AgentAssembler
from app.services.eah_agent.utils.stream_adapter import AgnoStreamAdapter
from app.services.eah_agent.document.file_orchestrator import FileOrchestrator

logger = logging.getLogger("eah.executors.fast")

class FastExecutor(LightBaseExecutor):
    """
    杞婚噺绾ф墽琛屽櫒 (Fast Executor)
    鍘?quick_handler.py 鍜?QuickAgent 鐨勫崌绾х増銆?
    涓撴敞浜庝綆寤惰繜銆侀珮鍙潬鐨勯棶绛斾笌鍗虫椂浜掑姩銆傝烦杩囦簡澶嶆潅鐨勮鍒掑拰鍙嶆€濈粍浠躲€?
    铻嶅悎浜?QuickAgent 涓殑浼樼鎸囦护绾︽潫銆?
    """

    SYSTEM_INSTRUCTIONS: List[str] = [
        "You are a helpful assistant operating in Fast mode 鈥?fast, accurate, and concise.",
        "When using web search or tools, always cite sources inline as [1], [2], 鈥? "
        "and append a **鍙傝€冭祫鏂?* section at the end of your answer.",
        "If a tool call fails or times out, acknowledge it honestly and answer "
        "from your existing knowledge instead of fabricating results.",
        "Keep answers focused; avoid unnecessary verbosity.",
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
        
        # 1. 璧勬簮瑁呴厤 (骞惰鎵ц锛氬姞杞藉巻鍙?+ 澶勭悊鏂囦欢)
        setup_tasks = [
            asyncio.create_task(self._prepare_agent(db, session_id, kwargs)),
            asyncio.create_task(self._prepare_history(session_id, current_query=input_text)),
            asyncio.create_task(self._handle_incoming_files(session_id, files))
        ]
        
        agent = await setup_tasks[0]
        if not agent:
            yield {"type": "error", "content": "Agent assembly failed"}
            return

        history_msgs = await setup_tasks[1]
        file_ctx, media_objs = await setup_tasks[2]

        # 2. 鎸囦护缂栨帓
        base_instructions = getattr(agent, "instructions", None)
        instructions = list(self.SYSTEM_INSTRUCTIONS)
        
        if isinstance(base_instructions, str):
            if base_instructions.strip(): instructions.append(base_instructions)
        elif isinstance(base_instructions, list):
            instructions.extend([str(x) for x in base_instructions if str(x).strip()])
            
        if file_ctx:
            instructions.append(f"Uploaded Files Context:\n{file_ctx}")
            yield {"type": "status", "content": f"Processed {len(files)} files."}

        # 3. 杈撳叆澧炲己
        augmented_input = self._augment_input(input_text, intent)

        # 4. 鎵ц娴佽緭鍑?
        try:
            async for chunk in agent.arun(
                augmented_input,
                messages=history_msgs,
                images=media_objs,
                instructions=instructions,
                stream=True
            ):
                async for event in self.stream_adapter.to_standard_events(chunk):
                    yield event
            
            async for event in self.stream_adapter.flush():
                yield event

        except Exception as e:
            logger.error(f"FastExecutor execution failed: {e}", exc_info=True)
            yield self._yield_error("Internal processing error", e)

    async def _prepare_agent(self, db: AsyncSession, session_id: str, kwargs: Any) -> Agent:
        """浠庤閰嶅櫒鑾峰彇 Agent 瀹炰緥"""
        agent_id = kwargs.get("agent_id")
        reasoning = kwargs.get("enable_reasoning", False)
        search = kwargs.get("enable_search", True)

        assembler = AgentAssembler(db, agent_id)
        return await assembler.build(
            session_id=session_id,
            reasoning_override=reasoning,
            enable_search=search
        )

    async def _handle_incoming_files(self, session_id: str, files: List[Any]) -> Tuple[str, List[Any]]:
        """骞惰澶勭悊涓婁紶鏂囦欢"""
        if not files:
            return "", []

        tasks = [
            FileOrchestrator.process_file(f.file, f.filename, session_id=session_id)
            for f in files
        ]
        results = await asyncio.gather(*tasks)
        
        contexts = []
        media = []
        for r in results:
            if r["status"] == "success":
                if r["content_text"]: contexts.append(r["content_text"])
                if r["media_objects"]: media.extend(r["media_objects"])
        
        return "\n\n".join(contexts), media

    def _augment_input(self, text: str, intent: Optional[IntentResult]) -> str:
        """鍩轰簬 NLU 鎰忓浘澧炲己杈撳叆"""
        if not intent or not intent.parameters:
            return text
        
        params = intent.parameters
        notes = []
        if "entities" in params: notes.append(f"Entities: {params['entities']}")
        if "time" in params: notes.append(f"Time Context: {params['time']}")
        
        if notes:
            return f"[Context: {' | '.join(notes)}]\n{text}"
        return text

