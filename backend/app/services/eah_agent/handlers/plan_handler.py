import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

# 核心架构组件
from app.services.eah_agent.core.agent_base_handler import BaseHandler, StreamResponse
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.services.eah_agent.core.agent_builder import AgentAssembler
from app.services.eah_agent.core.agent_orchestrator import AgentWorkflowEngine
from app.services.eah_agent.document.file_orchestrator import FileOrchestrator
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor
from app.core.i18n import _

logger = logging.getLogger("eah.handler.plan")

class PlanHandler(BaseHandler):
    """
    自主规划处理器：负责高复杂性、多阶段任务的调度与执行引擎触发。
    """

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

        yield {"type": "status", "content": _("Orchestrating autonomous planning environment...")}

        # 1. 资源并行装配 (Resource Parallelism)
        # 同时启动：智能体装配、文件多模态解析、历史上下文压缩
        setup_tasks = [
            asyncio.create_task(self._assemble_plan_agent(db, agent_id, session_id)),
            asyncio.create_task(FileOrchestrator.process_batch(files, session_id)), # 假设支持批量处理
            asyncio.create_task(self._prepare_history(db, session_id, current_query=input_text))
        ]

        # 2. 等待资源就绪
        agent, file_results, (history_msgs, _was_compressed) = await asyncio.gather(*setup_tasks)

        # 2. 动态指令合成 (Instruction Synthesis)
        base_instructions = getattr(agent, "instructions", None)
        if isinstance(base_instructions, str):
            instructions = [base_instructions] if base_instructions.strip() else []
        elif isinstance(base_instructions, list):
            instructions = [str(x) for x in base_instructions if str(x).strip()]
        else:
            instructions = []
        
        # 注入多模态上下文与意图增强
        if file_results["context"]:
            instructions.append(f"Environment Context (Files):\n{file_results['context']}")
            yield {"type": "status", "content": _("Contextualized with {} files.").format(len(files))}
            
        if intent and intent.parameters:
            instructions.append(f"Extraction Hints: {intent.parameters}")

        # 3. 增强任务目标
        # 强制要求 Agent 遵循依赖感知的规划协议
        enriched_goal = self._enrich_goal(input_text, "\n\n".join(instructions))

        # 4. 移交工作流引擎 (Engine Delegation)
        # P10 准则：Handler 不自己跑循环，而是启动专门的状态机引擎
        try:
            workflow_engine = AgentWorkflowEngine(db=db)
            
            # 这里的 workflow_engine 内部会处理 PlannerAgent 的创建、
            # update_plan 拦截、DAG 持久化以及后续 Executor 的并行触发。
            async for event in workflow_engine.start_workflow(
                session_id=session_id,
                user_goal=enriched_goal,
                agent_instance=agent, # 注入已经装配好的 Agent
                media_objects=file_results["media"]
            ):
                yield event

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            yield {"type": "error", "content": _("Planning engine encountered a critical failure.")}

    # --- 私有辅助方法 ---

    async def _assemble_plan_agent(self, db: AsyncSession, agent_id: str, session_id: str) -> Any:
        """委托 Assembler 处理复杂的资源挂载（MCP, E2B, Tools）"""
        assembler = AgentAssembler(db, agent_id)
        return await assembler.build(
            session_id=session_id,
            reasoning_override=True, # 规划模式强制开启推理
            enable_plan_tools=True,  # 告诉装配器需要 PlanTools
            enable_file_tools=True   # 告诉装配器需要 FileTools
        )

    async def _prepare_history(self, db: AsyncSession, session_id: str, current_query: str = "") -> Tuple[List[Dict], bool]:
        """加载并压缩历史消息，融入图谱记忆"""
        return await self._get_history_messages_with_graph(db, session_id, current_query)

    def _enrich_goal(self, text: str, full_instructions: str) -> str:
        """封装最终发给引擎的任务描述"""
        return (
            f"SYSTEM_INSTRUCTIONS:\n{full_instructions}\n\n"
            f"USER_GOAL:\n{text}\n\n"
            "MISSION: Break down into steps, respect dependencies, and execute."
        )
