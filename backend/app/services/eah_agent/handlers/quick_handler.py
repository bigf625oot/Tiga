import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

# 核心依赖
from app.services.eah_agent.core.agent_base_handler import BaseHandler, StreamResponse
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.services.eah_agent.core.agent_builder import AgentAssembler
from app.services.eah_agent.core.agent_stream_adapter import AgnoStreamAdapter  # 抽象出的流适配器
from app.services.eah_agent.document.file_orchestrator import FileOrchestrator # 之前重构的文件处理器
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor
from app.core.shared_state import StateManager

logger = logging.getLogger("eah.handler.quick")

class QuickHandler(BaseHandler):
    """
    极速处理器：专注于低延迟、高可靠的问答与即时互动。
    """

    def __init__(self, llm_model: Optional[Any] = None):
        super().__init__(llm_model)
        self.stream_adapter = AgnoStreamAdapter()

    async def process(
        self, 
        input_text: str, 
        intent: Optional[IntentResult] = None, 
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        db: AsyncSession = kwargs.get("db")
        session_id: str = kwargs.get("session_id")
        files: List[Any] = kwargs.get("files", [])
        
        # 1. 资源装配 (并行执行：加载历史 + 处理文件 + 意图增强)
        # P10 技巧：在等待 Agent 初始化的同时，并发处理 IO 密集型任务
        setup_tasks = [
            asyncio.create_task(self._prepare_agent(db, session_id, kwargs)),
            asyncio.create_task(self._prepare_history(db, session_id, current_query=input_text)),
            asyncio.create_task(self._handle_incoming_files(session_id, files))
        ]
        
        # 先获取 Agent，因为它决定了后续如何注入上下文
        agent = await setup_tasks[0]
        if not agent:
            yield {"type": "error", "content": "Agent assembly failed"}
            return

        # 获取其余结果
        history_msgs, was_compressed = await setup_tasks[1]
        file_ctx, media_objs = await setup_tasks[2]

        if was_compressed:
            yield {"type": "status", "content": "Context compressed due to length."}

        # 2. 指令编排 (Prompt Orchestration)
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

        # 3. 输入增强 (Input Augmentation)
        augmented_input = self._augment_input(input_text, intent)

        # 4. 执行流输出
        try:
            # 统一流适配器处理复杂的 Agno 事件映射
            async for chunk in agent.arun(
                augmented_input,
                messages=history_msgs,
                images=media_objs,
                # 动态覆盖指令
                instructions=instructions,
                stream=True
            ):
                # 将 Agno 原生块转换为标准的 StreamResponse
                async for event in self.stream_adapter.to_standard_events(chunk):
                    yield event
            
            # Flush the stream adapter buffer
            async for event in self.stream_adapter.flush():
                yield event

        except Exception as e:
            logger.error(f"QuickHandler execution failed: {e}", exc_info=True)
            yield {"type": "error", "content": f"Internal processing error: {str(e)}"}

    # --- 私有编排方法 ---

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

    async def _prepare_history(self, db: AsyncSession, session_id: str, current_query: str = "") -> Tuple[List[Dict], bool]:
        """加载并压缩历史消息，融入图谱记忆"""
        return await self._get_history_messages_with_graph(db, session_id, current_query)

    async def _handle_incoming_files(self, session_id: str, files: List[Any]) -> Tuple[str, List[Any]]:
        """并行处理上传文件"""
        if not files:
            return "", []

        # 调用重构后的 FileOrchestrator
        # P10 优化：并行处理所有文件
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
        
        # 提取参数并注入
        params = intent.parameters
        notes = []
        if "entities" in params: notes.append(f"Entities: {params['entities']}")
        if "time" in params: notes.append(f"Time Context: {params['time']}")
        
        if notes:
            return f"[Context: {' | '.join(notes)}]\n{text}"
        return text
