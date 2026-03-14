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
from typing import AsyncGenerator, Dict, Any, Optional
from app.services.eah_agent.core.base_handler import BaseHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.services.eah_agent.core.agent_factory import AgentFactory
from app.services.eah_agent.domain.config import AgentConfig
from app.core.i18n import _
from app.models.llm_model import LLMModel
from agno.agent import Agent

logger = logging.getLogger(__name__)

class PlanHandler(BaseHandler):
    """
    Handles 'task' intent with autonomous planning (ReAct).
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)
        self.agent: Optional[Agent] = None
        # Agent initialization is deferred to the first process call

    async def _ensure_agent_initialized(self):
        """
        Lazily initialize the agent using AgentFactory.
        """
        if not self.agent and self.llm_model:
            try:
                # Create a default config for PlanHandler
                # TODO: In the future, load this from DB or make it dynamic
                config = AgentConfig(
                    name="PlanAgent",
                    role="You are an autonomous agent capable of planning and executing tasks.",
                    instructions=["Think step-by-step.", "Use tools when necessary."],
                    tools=[], # Load default tools if any
                    skills=[], # Add default skills here if needed
                    reasoning=True,
                    model_params={"temperature": 0.1} # Lower temp for planning
                )
                
                self.agent = await AgentFactory.create_agent(config, llm_model=self.llm_model)
            except Exception as e:
                logger.error(f"Failed to create agent for PlanHandler: {e}")
                self.agent = None

    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        await self._ensure_agent_initialized()
        
        if not self.agent:
             yield {"type": "error", "content": _("Agent not initialized for PlanHandler.")}
             return

        try:
            yield {"type": "status", "content": _("Analyzing task...")}
            
            # Execute the agent with streaming
            # Assuming agent.run(stream=True) returns a generator
            response_stream = self.agent.run(input_text, stream=True)
            
            for chunk in response_stream:
                # Extract content from the chunk
                # Assuming chunk is an object with a 'content' attribute
                content = getattr(chunk, 'content', None)
                
                # Check for reasoning/thought process if available
                # Some models/frameworks might separate this
                # For now, we assume Agno might include it in content or we rely on downstream parsing
                
                if content:
                     yield {"type": "content", "content": content}
                elif isinstance(chunk, str):
                     yield {"type": "content", "content": chunk}

        except Exception as e:
            logger.error(f"PlanHandler processing failed: {e}")
            yield {"type": "error", "content": _("I encountered an error while planning.")}
