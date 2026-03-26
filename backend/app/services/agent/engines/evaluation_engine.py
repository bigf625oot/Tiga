import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.models.llm_model import LLMModel
from app.services.platform.llm.factory import ModelFactory

logger = logging.getLogger("eah.core.engines.evaluation")

class EvaluationEngine:
    """
    评估引擎 (Evaluation Engine)
    负责对 ExecutionEngine 输出的结果进行质量打分和规则校验，
    判断任务是否真正达成，或者是否需要重试/重新规划。
    """
    def __init__(self, db: AsyncSession, llm_model: Optional[LLMModel] = None):
        self.db = db
        self.llm_model = llm_model

    async def evaluate_result(self, task_goal: str, execution_result: str, criteria: str) -> Dict[str, Any]:
        """
        评估执行结果是否满足预期。
        返回格式例如: {"passed": True/False, "score": 1-10, "feedback": "..."}
        """
        if not self.llm_model:
            from app.services.platform.llm.resolver import resolve_chat_llm_model
            self.llm_model = await resolve_chat_llm_model(self.db)
            
        model_instance = ModelFactory.create_model(self.llm_model)
        
        evaluator = Agent(
            name="Evaluator",
            model=model_instance,
            instructions=[
                "You are an objective evaluator.",
                "Review the execution result against the task goal and acceptance criteria.",
                "You must output ONLY valid JSON containing 'passed' (boolean), 'score' (1-10), and 'feedback' (string)."
            ],
            markdown=False
        )

        prompt = (
            f"Task Goal: {task_goal}\n"
            f"Criteria: {criteria}\n"
            f"Execution Result:\n{execution_result}\n\n"
            "Evaluate now."
        )

        try:
            response = await evaluator.arun(prompt)
            content = response.content if hasattr(response, 'content') else response
            
            import json
            import re
            
            # Clean up potential markdown formatting
            cleaned_content = content.strip()
            if cleaned_content.startswith("```"):
                # Use regex to find content between ```json and ``` or just ``` and ```
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned_content, re.DOTALL)
                if match:
                    cleaned_content = match.group(1).strip()
            
            # 这里简单做一下 JSON 解析，实际生产可以借助 pydantic Schema
            try:
                result = json.loads(cleaned_content)
                return {
                    "passed": result.get("passed", True),
                    "score": result.get("score", 10),
                    "feedback": result.get("feedback", "No feedback provided.")
                }
            except json.JSONDecodeError:
                logger.warning(f"Evaluation returned invalid JSON: {content}")
                # Why failed=True by default: a parse failure means we cannot confirm the task passed.
                # Returning passed=True would silently disable the retry guard.
                return {"passed": False, "score": 0, "feedback": f"Evaluator output was not valid JSON: {content[:200]}"}

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"passed": False, "score": 0, "feedback": f"Evaluation engine error: {e}"}

    async def reflect(self, task_goal: str, execution_result: str, feedback: str) -> str:
        """
        基于失败的评估结果，生成针对下一步执行的改进建议（Reflection）。
        """
        if not self.llm_model:
            from app.services.platform.llm.resolver import resolve_chat_llm_model
            self.llm_model = await resolve_chat_llm_model(self.db)
            
        model_instance = ModelFactory.create_model(self.llm_model)
        
        reflector = Agent(
            name="Reflector",
            model=model_instance,
            instructions=[
                "You are an expert technical reflector.",
                "Based on the task goal, execution result, and failure feedback, provide a concise and actionable hint on how to fix the issue in the next attempt.",
                "Output ONLY the actionable hint."
            ],
            markdown=False
        )

        prompt = (
            f"Task Goal: {task_goal}\n"
            f"Execution Result: {execution_result}\n"
            f"Failure Feedback: {feedback}\n\n"
            "Provide actionable advice for the next execution attempt:"
        )

        try:
            response = await reflector.arun(prompt)
            content = response.content if hasattr(response, 'content') else response
            return content.strip()
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            return "Please review the previous failure and adjust the strategy."
