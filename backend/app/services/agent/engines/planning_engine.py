import logging
import asyncio
import hashlib
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.models.llm_model import LLMModel
from app.services.platform.llm.factory import ModelFactory
from app.services.agent.schemas.plan import PlanValidationError, TaskPlan, parse_task_plan, ExecutionPlan, ExecutionTaskStep
import uuid

logger = logging.getLogger("eah.core.engines.planning")

class PlanningEngine:
    """
    规划引擎 (Planning Engine)
    负责将用户的复杂目标拆解为有向无环图 (DAG) 结构的任务流。
    具有 Self-Correction (自我纠错) 能力。
    """
    def __init__(self, db: AsyncSession, llm_model: Optional[LLMModel] = None):
        self.db = db
        self.llm_model = llm_model
        self._agent: Optional[Agent] = None
        self._init_lock = asyncio.Lock()

    async def _ensure_agent(self) -> Agent:
        if self._agent:
            return self._agent
            
        async with self._init_lock:
            if not self._agent:
                if not self.llm_model:
                    from app.services.platform.llm.resolver import resolve_chat_llm_model
                    self.llm_model = await resolve_chat_llm_model(self.db)
                
                model_instance = ModelFactory.create_model(self.llm_model)

                self._agent = Agent(
                    name="Lead-Architect-Planner",
                    model=model_instance,
                    instructions=[
                        "你是一位资深系统架构师，负责将复杂的业务目标拆解为可执行的任务流。",
                        "【极简原则】：如果用户目标可以通过一次生成或查询完成（例如写一篇文章、生成测试用例、回答问题、写一段代码），请只输出 1 个任务步骤！不要过度设计！",
                        "只有在涉及多个异构系统调用或需要强制的先后依赖（如先搜索再汇总）时，才拆分为多个步骤。",
                        "每个任务必须是原子性的，且有明确的 'expected_output'。",
                        "你必须明确任务间的依赖关系，严禁产生循环依赖。",
                        "仅输出一个 JSON 对象，不要解释，不要 Markdown，不要代码块。",
                        "JSON 顶层必须包含 keys: steps, estimated_reasoning。",
                        "steps 是数组；每个元素必须包含: id(int), task(str), tool_name(str), dependencies(int[])。",
                        "id 从 1 开始递增；dependencies 只能引用已出现的更小 id。",
                        "estimated_reasoning 用于解释规划策略。"
                    ],
                    retries=3,
                    markdown=False,
                )
        return self._agent

    async def generate_plan(self, session_id: str, user_goal: str, context: str = "") -> ExecutionPlan:
        """
        生成并校验计划，返回 PlanManifest 对象。
        不负责持久化，持久化交由 StateManager 或上层 Executor 处理。
        """
        logger.info(f"Initiating planning for session: {session_id}")
        agent = await self._ensure_agent()
        agent.output_schema = TaskPlan

        base_prompt = (
            f"User Goal: {user_goal}\n"
            f"Contextual Info: {context}\n\n"
            "【CRITICAL】: If the User Goal is a simple generation task (like writing a document, test case, code, or answering a question), you MUST output exactly ONE step. "
            "Do NOT split it into multiple steps like 'analyze', 'write part 1', 'write part 2', 'review'. The executor is highly capable and can do it in one go.\n"
            "Please ensure that the 'task' description and 'estimated_reasoning' "
            "are in the same language as the User Goal."
        )

        MAX_SELF_CORRECTION_ROUNDS = 3
        last_error: Optional[Exception] = None
        last_raw: str = ""

        for attempt in range(1, MAX_SELF_CORRECTION_ROUNDS + 1):
            if attempt == 1:
                prompt = base_prompt
            else:
                error_feedback = self._format_error_feedback(last_error, last_raw)
                prompt = (
                    f"{base_prompt}\n\n"
                    f"--- SELF-CORRECTION ROUND {attempt} ---\n"
                    f"Your previous response failed validation. Fix the issues below and output ONLY valid JSON:\n"
                    f"{error_feedback}"
                )
                logger.warning(f"[PlanningEngine] Self-correction attempt {attempt}/{MAX_SELF_CORRECTION_ROUNDS} for session {session_id}: {last_error}")

            try:
                response = await agent.arun(prompt)
                raw_plan = response.content if hasattr(response, "content") else response
                last_raw = raw_plan if isinstance(raw_plan, str) else str(raw_plan)

                plan = parse_task_plan(raw_plan)

                manifest = ExecutionPlan(
                    plan_id=f"plan-{uuid.uuid4()}",
                    session_id=session_id,
                    reasoning=plan.estimated_reasoning,
                    tasks=[
                        ExecutionTaskStep(
                            task_id=str(step.id),
                            title=step.task[:90],
                            description=step.task,
                            dependencies=[str(d) for d in step.dependencies],
                            executor_role=step.tool_name,
                            expected_output="Execute successfully",
                        )
                        for step in plan.steps
                    ],
                )
                
                # Validation is handled in PlanManifest's Pydantic validator
                if attempt > 1:
                    logger.info(f"[PlanningEngine] Self-correction succeeded on attempt {attempt}.")
                return manifest

            except PlanValidationError as e:
                last_error = e
                sha = hashlib.sha256(last_raw.encode("utf-8", errors="ignore")).hexdigest()[:12]
                logger.error(f"[PlanningEngine] Attempt {attempt} validation failed (sha={sha}): {e}")
                if attempt == MAX_SELF_CORRECTION_ROUNDS:
                    raise PlanValidationError(f"Plan validation failed after {MAX_SELF_CORRECTION_ROUNDS} attempts: {e}")

        raise RuntimeError("Unexpected exit from planning loop")

    @staticmethod
    def _format_error_feedback(error: Optional[Exception], raw_output: str) -> str:
        lines = []
        if isinstance(error, PlanValidationError) and error.validation_details:
            lines.append("Validation errors found:")
            for detail in error.validation_details:
                path = detail.get("path", "?")
                issue = detail.get("issue", "?")
                lines.append(f"  - Field '{path}': {issue}")
        elif error:
            lines.append(f"Error: {error}")

        snippet = raw_output[:1200].replace("\n", " ")
        lines.append(f"\nYour previous output (first 1200 chars): {snippet}")
        return "\n".join(lines)
