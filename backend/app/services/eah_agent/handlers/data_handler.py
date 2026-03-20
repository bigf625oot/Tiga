import logging
import asyncio
import json
import re
import time
from typing import AsyncGenerator, Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

# 核心架构组件
from app.services.eah_agent.core.agent_base_handler import BaseHandler, StreamResponse
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.services.eah_agent.core.agent_builder import AgentAssembler
from app.services.eah_agent.document.file_orchestrator import FileOrchestrator
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor
from app.core.i18n import _

logger = logging.getLogger("eah.handler.data")

# =================================================================
# DataHandler: 数据分析专家处理器
# =================================================================

class DataHandler(BaseHandler):
    """
    数据分析专家处理器：负责 SQL 生成、可视化及 CSV/Excel 分析。
    """

    def __init__(self, llm_model: Optional[Any] = None):
        super().__init__(llm_model)
        from app.services.eah_agent.core.agent_stream_adapter import AgnoStreamAdapter
        self.stream_adapter = AgnoStreamAdapter(extract_charts=True)

    async def process(
        self, 
        input_text: str, 
        intent: Optional[IntentResult] = None, 
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        db: AsyncSession = kwargs.get("db")
        session_id: str = kwargs.get("session_id")
        files: List[Any] = kwargs.get("files", [])
        agent_id: str = kwargs.get("agent_id")

        yield {"type": "status", "content": _("Warming up Data Analyst Engine...")}

        # 1. 并行资源准备 (并行加载 Agent、文件、历史记录)
        setup_tasks = [
            asyncio.create_task(self._assemble_data_agent(db, agent_id, session_id)),
            asyncio.create_task(FileOrchestrator.process_batch(files, session_id)),
            asyncio.create_task(self._prepare_history(db, session_id))
        ]

        # 等待所有前置任务完成
        agent, file_results, (history_msgs, _was_compressed) = await asyncio.gather(*setup_tasks)

        # 2. 指令编排
        base_instructions = getattr(agent, "instructions", None)
        if isinstance(base_instructions, str):
            instructions = [base_instructions] if base_instructions.strip() else []
        elif isinstance(base_instructions, list):
            instructions = [str(x) for x in base_instructions if str(x).strip()]
        else:
            instructions = []
        if file_results.get("context"):
            instructions.append(f"Available Local Data Context:\n{file_results['context']}")
            yield {"type": "status", "content": _("Connected to {} local data sources.").format(len(files))}

        # 3. 执行分析流
        try:
            yield {"type": "status", "content": _("Analyzing dataset and generating insights...")}
            
            async for chunk in agent.arun(
                input_text,
                messages=history_msgs,
                instructions=instructions,
                # file_paths=file_results.get("paths", []), # Assuming Agno arun supports file_paths or need adjustment
                stream=True
            ):
                # 通过适配器转换 Chunk
                async for event in self.stream_adapter.to_standard_events(chunk):
                    yield event
            
            # 最后冲刷缓冲区
            async for event in self.stream_adapter.flush():
                yield event

        except Exception as e:
            logger.error(f"Data analysis critical failure: {e}", exc_info=True)
            yield {"type": "error", "content": _("I encountered an issue while processing the data.")}

    # --- 私有逻辑 ---

    async def _assemble_data_agent(self, db: AsyncSession, agent_id: str, session_id: str) -> Agent:
        assembler = AgentAssembler(db, agent_id)
        return await assembler.build(
            session_id=session_id,
            enable_data_tools=True,
            enable_coding_tools=True,
            enable_sandbox=True,
            reasoning_override=True
        )

    async def _prepare_history(self, db: AsyncSession, session_id: str) -> Tuple[List[Dict], bool]:
        if not session_id or not db: return [], False
        history = SessionHistory(db)
        msgs = await history.get_messages(session_id, limit=10)
        compressor = ContextCompressor(model=self.llm_model)
        compressed = await compressor.compress_context(
            [{"role": m.role, "content": m.content} for m in msgs], 
            max_tokens=2000
        )
        return compressed, len(compressed) < len(msgs)
