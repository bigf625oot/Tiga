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
from app.services.eah_agent.core.agent_assembler import AgentAssembler
from app.services.eah_agent.handlers.file_orchestrator import FileOrchestrator
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor
from app.core.i18n import _

logger = logging.getLogger("eah.handler.data")

# =================================================================
# AgnoStreamAdapter: 流式协议编排引擎
# =================================================================

class AgnoStreamAdapter:
    """
    P10 级流式内容转换器。
    职责：
    1. 增量缓冲：处理跨 Chunk 的 Delimiter (:::) 识别。
    2. 块提取：从文本流中剥离 JSON 图表块，防止 UI 渲染原始 JSON。
    3. 协议标准化：将 Agno 内部对象统一为前端可识别的事件字典。
    """

    def __init__(self, extract_charts: bool = True):
        self.extract_charts = extract_charts
        self._text_buffer = ""
        self._in_block = False
        self._block_type: Optional[str] = None
        
        # 识别协议：::: echarts {json} :::
        self.BLOCK_START_PATTERN = re.compile(r":::\s*(\w+)")
        self.BLOCK_END_TAG = ":::"

    async def to_standard_events(self, chunk: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """将 Agno 原生 Chunk 转换为标准化事件流"""
        
        # 1. 处理 RunOutput 元数据（包含最终统计、消耗等）
        if type(chunk).__name__ == "RunOutput":
            yield {"type": "run_output", "data": self._safe_to_dict(chunk)}
            return

        # 2. 处理工具调用状态 (Tool Calling)
        if hasattr(chunk, "tool_calls") and chunk.tool_calls:
            names = [tc.function.name for tc in chunk.tool_calls if tc.function]
            if names:
                yield {"type": "status", "content": _("Running tools: {}...").format(', '.join(names))}

        # 3. 处理思考流 (Reasoning/Think)
        # 适配不同模型的思维链字段名
        reasoning = getattr(chunk, "reasoning", None) or getattr(chunk, "reasoning_content", None)
        if reasoning:
            yield {"type": "think", "content": reasoning}

        # 4. 核心：处理文本增量与块提取
        content = getattr(chunk, "content", None)
        if content:
            async for event in self._process_content_delta(content):
                yield event

    async def _process_content_delta(self, new_text: str) -> AsyncGenerator[Dict[str, Any], None]:
        """增量文本处理逻辑：实现状态机提取"""
        self._text_buffer += new_text

        while True:
            if not self._in_block:
                # 寻找块开始标志 :::
                match = self.BLOCK_START_PATTERN.search(self._text_buffer)
                if match:
                    # 吐出块之前的文本
                    pre_text = self._text_buffer[:match.start()]
                    if pre_text:
                        yield {"type": "content", "content": pre_text}
                    
                    self._in_block = True
                    self._block_type = match.group(1)
                    self._text_buffer = self._text_buffer[match.end():]
                    continue
                else:
                    # 没找到开始标志，但要保留末尾几个字符（防止 ::: 被切割在两个包里）
                    safe_len = max(0, len(self._text_buffer) - 10)
                    to_send = self._text_buffer[:safe_len]
                    if to_send:
                        yield {"type": "content", "content": to_send}
                        self._text_buffer = self._text_buffer[safe_len:]
                    break
            else:
                # 寻找块结束标志 :::
                end_idx = self._text_buffer.find(self.BLOCK_END_TAG)
                if end_idx != -1:
                    raw_block = self._text_buffer[:end_idx].strip()
                    # 提取并解析
                    yield self._handle_block(self._block_type, raw_block)
                    
                    self._in_block = False
                    self._block_type = None
                    self._text_buffer = self._text_buffer[end_idx + len(self.BLOCK_END_TAG):]
                    continue
                else:
                    # 块还没结束，继续在 buffer 中堆积，不 yield content
                    break

    def _handle_block(self, btype: str, raw_content: str) -> Dict[str, Any]:
        """处理提取出来的块内容"""
        if btype == "echarts" and self.extract_charts:
            try:
                data = json.loads(raw_content)
                return {"type": "chart", "content": data, "sub_type": "echarts"}
            except Exception as e:
                logger.warning(f"Echarts JSON parse failed: {e}")
                return {"type": "content", "content": f"\n```json\n{raw_content}\n```\n"}
        
        # 默认作为代码块回退
        return {"type": "content", "content": f"\n```{btype}\n{raw_content}\n```\n"}

    async def flush(self) -> AsyncGenerator[Dict[str, Any], None]:
        """流结束时强制清空缓冲区"""
        if self._text_buffer:
            if self._in_block:
                yield self._handle_block(self._block_type, self._text_buffer)
            else:
                yield {"type": "content", "content": self._text_buffer}
        self._text_buffer = ""

    def _safe_to_dict(self, obj: Any) -> Dict[str, Any]:
        try:
            return obj.to_dict() if hasattr(obj, "to_dict") else str(obj)
        except:
            return {}

# =================================================================
# DataHandler: 数据分析专家处理器
# =================================================================

class DataHandler(BaseHandler):
    """
    数据分析专家处理器：负责 SQL 生成、可视化及 CSV/Excel 分析。
    """

    def __init__(self, llm_model: Optional[Any] = None):
        super().__init__(llm_model)
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
        agent, file_results, (history_msgs, _) = await asyncio.gather(*setup_tasks)

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
            
            async for chunk in agent.astream(
                input_text,
                messages=history_msgs,
                instructions=instructions,
                file_paths=file_results.get("paths", []) 
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
        assembler = AgentAssembler(db)
        return await assembler.assemble(
            agent_id=agent_id,
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
