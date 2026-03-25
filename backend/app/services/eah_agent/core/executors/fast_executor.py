import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.models.llm_model import LLMModel
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.services.eah_agent.core.executors.light_base_executor import LightBaseExecutor
from app.services.eah_agent.core.components.default_memory_manager import DefaultMemoryManager
from app.services.eah_agent.core.agent_builder import AgentAssembler
from app.services.eah_agent.core.agent_stream_adapter import AgnoStreamAdapter
from app.services.eah_agent.document.file_orchestrator import FileOrchestrator

logger = logging.getLogger("eah.executors.fast")

class FastExecutor(LightBaseExecutor):
    """
    轻量级执行器 (Fast Executor)
    原 quick_handler.py 的升级版。
    专注于低延迟、高可靠的问答与即时互动。跳过了复杂的规划和反思组件。
    """

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
        
        # 1. 资源装配 (并行执行：加载历史 + 处理文件)
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

        # 2. 指令编排
        base_instructions = getattr(agent, "instructions", None)
        if isinstance(base_instructions, str):
            instructions = [base_instructions] if base_instructions.strip() else []
        elif isinstance(base_instructions, list):
            instructions = [str(x) for x in base_instructions if str(x).strip()]
        else:
            instructions = []
            
        if file_ctx:
            instructions.append(f"Uploaded Files Context:\n{file_ctx}")
            yield {"type": "status", "content": f"Processed {len(files)} files."}

        # 3. 输入增强
        augmented_input = self._augment_input(input_text, intent)

        # 4. 执行流输出
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
            yield {"type": "error", "content": f"Internal processing error: {str(e)}"}

    async def _prepare_agent(self, db: AsyncSession, session_id: str, kwargs: Any) -> Agent:
        """从装配器获取 Agent 实例"""
        agent_id = kwargs.get("agent_id")
        reasoning = kwargs.get("enable_reasoning", False)
        search = kwargs.get("enable_search", True)

        assembler = AgentAssembler(db, agent_id)
        return await assembler.build(
            session_id=session_id,
            reasoning_override=reasoning,
            enable_search=search
        )

    async def _prepare_history(self, session_id: str, current_query: str = "") -> List[Dict]:
        """通过 MemoryManager 加载并压缩历史消息"""
        if self.memory_manager:
            return await self.memory_manager.get_compressed_context(session_id, current_query)
        return []

    async def _handle_incoming_files(self, session_id: str, files: List[Any]) -> Tuple[str, List[Any]]:
        """并行处理上传文件"""
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
        """基于 NLU 意图增强输入"""
        if not intent or not intent.parameters:
            return text
        
        params = intent.parameters
        notes = []
        if "entities" in params: notes.append(f"Entities: {params['entities']}")
        if "time" in params: notes.append(f"Time Context: {params['time']}")
        
        if notes:
            return f"[Context: {' | '.join(notes)}]\n{text}"
        return text
