from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from agno.agent import Agent
from app.services.platform.llm.factory import ModelFactory
from app.models.llm_model import LLMModel

class ClarificationResult(BaseModel):
    is_ambiguous: bool = Field(description="判断用户意图是否模糊或缺失执行复杂任务所必须的关键信息。")
    clarification_question: Optional[str] = Field(description="如果模糊，提出一个精炼的反问以获取关键缺失信息。如果清晰，返回 null。")
    reasoning: str = Field(description="判断的简短推理过程。")

class IntentClarifier:
    """
    轻量级意图澄清器 (Lightweight Intent Clarifier)
    作为复杂任务规划前的前置网关，防止无效的高成本 Planning 计算。
    """
    def __init__(self, llm_model: Optional[LLMModel] = None):
        # 默认采用与全局一致的模型，但在实际生产中建议注入较小/较快的模型 (如 gpt-4o-mini 或 deepseek-chat)
        self.model = ModelFactory.create_model(llm_model) if llm_model else None
        
        self.agent = Agent(
            model=self.model,
            description="你是一个高级任务前置分析器。你的任务是在系统执行复杂的步骤规划前，判断用户的请求是否足够清晰、是否具备必要的上下文信息。",
            instructions=[
                "1. 仔细分析用户的输入和提供的上下文（如果有）。",
                "2. 这是一个 'Task'（任务执行）场景。判断用户是否提供了执行任务的明确目标和关键参数。",
                "3. 如果输入非常宽泛、模糊（例如只有'帮我写个代码'、'分析一下数据'而没有具体方向），必须判断为模糊（is_ambiguous=True）。",
                "4. 如果判断为模糊，请直接输出一句友好、专业的反问句（clarification_question），引导用户提供缺失的信息。",
                "5. 你的响应必须是严格的 JSON 格式。"
            ],
            output_schema=ClarificationResult,
            markdown=False
        )

    async def check_ambiguity(self, input_text: str, context: str = "") -> ClarificationResult:
        """
        检查输入的模糊性
        """
        prompt = f"用户输入: {input_text}\n"
        if context:
            prompt += f"已有上下文/文件信息: {context}\n"
        
        prompt += "\n请判断该任务是否需要反问澄清？"
        
        try:
            # 采用强结构的响应模型
            response = await self.agent.arun(prompt)
            return response.content
        except Exception as e:
            # 托底策略：如果澄清器自身发生异常，降级为“放行”，由下游引擎自行处理
            return ClarificationResult(
                is_ambiguous=False,
                clarification_question=None,
                reasoning=f"Clarifier failed, fallback to pass: {str(e)}"
            )
