import logging
import json
import re
from typing import List, Literal, Optional, Any
from pydantic import BaseModel, Field, AliasChoices, field_validator
from app.workflow.context import AgentContext
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.llm_model import LLMModel
from app.services.llm.factory import ModelFactory
import asyncio

logger = logging.getLogger(__name__)

_DURATION_RE = re.compile(r"^\s*(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>ms|s|m|h)?\s*$", re.IGNORECASE)

def _parse_duration_seconds(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        m = _DURATION_RE.match(value)
        if not m:
            raise ValueError("Invalid duration format")
        num = float(m.group("num"))
        unit = (m.group("unit") or "s").lower()
        if unit == "ms":
            return num / 1000.0
        if unit == "s":
            return num
        if unit == "m":
            return num * 60.0
        if unit == "h":
            return num * 3600.0
    raise TypeError("Invalid duration type")

class PlanStepItem(BaseModel):
    step_id: int = Field(..., description="Sequence number of the step")
    operation: Literal["retrieve", "execute", "persist", "finish"] = Field(..., description="The operation type")
    description: str = Field(..., description="Detailed description of the operation")
    dependencies: List[int] = Field(default_factory=list, description="List of step_ids this step depends on")
    estimated_time: float = Field(
        0.0,
        ge=0,
        description="Estimated time in seconds",
        validation_alias=AliasChoices("estimated_time", "time_estimate"),
    )
    required_resources: List[str] = Field(default_factory=list, description="List of resources needed (e.g., 'knowledge_base', 'search_tool')")

    @field_validator("estimated_time", mode="before")
    @classmethod
    def _coerce_estimated_time(cls, v: Any) -> float:
        return _parse_duration_seconds(v)

class ExecutionPlan(BaseModel):
    steps: List[PlanStepItem] = Field(..., description="List of executable steps")
    reasoning: str = Field("", description="Reasoning for the plan")

def _normalize_plan_payload(payload: Any) -> dict:
    if isinstance(payload, list):
        return {"steps": payload, "reasoning": ""}
    if isinstance(payload, dict):
        if "steps" not in payload and "step" in payload and isinstance(payload["step"], list):
            payload = {**payload, "steps": payload["step"]}
        if "reasoning" not in payload:
            payload = {**payload, "reasoning": ""}
        return payload
    raise TypeError("Plan payload must be an object or list")

def _parse_execution_plan(content_str: str) -> ExecutionPlan:
    content_str = content_str.strip()
    if content_str.startswith("```"):
        content_str = content_str.split("\n", 1)[1].strip()
        if content_str.endswith("```"):
            content_str = content_str[:-3].strip()
    payload = json.loads(content_str)
    payload = _normalize_plan_payload(payload)
    return ExecutionPlan.model_validate(payload)

async def plan_step(context: AgentContext) -> AgentContext:
    """
    Step to dynamically plan the next steps using an LLM.
    Returns a list of executable steps.
    """
    try:
        # 1. Resolve Planner Model (Priority: Agent Config -> Active Model -> Global Key)
        planner_model = None
        
        async with AsyncSessionLocal() as db:
            try:
                # 1.1 Try to load from Agent Config
                if context.agent_id:
                    from app.models.agent import Agent as AgentModel
                    res = await db.execute(select(AgentModel).filter(AgentModel.id == context.agent_id))
                    agent_obj = res.scalars().first()
                    
                    if agent_obj and agent_obj.model_config:
                        target_model_id = agent_obj.model_config.get("model_id")
                        if target_model_id:
                             # Find the LLMModel definition
                             res = await db.execute(select(LLMModel).filter(LLMModel.model_id == target_model_id))
                             llm_obj = res.scalars().first()
                             if llm_obj:
                                 planner_model = ModelFactory.create_model(llm_obj)
                                 logger.info(f"Planner using Agent-specific model: {llm_obj.model_id}")

                # 1.2 Fallback to Active Model (if not set by Agent)
                if not planner_model:
                    # Try to find an active model
                    res = await db.execute(
                        select(LLMModel)
                        .filter(LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
                        .order_by(LLMModel.updated_at.desc())
                    )
                    active_model = res.scalars().first()
                    
                    if active_model:
                        planner_model = ModelFactory.create_model(active_model)
                        logger.info(f"Planner using active model: {active_model.model_id}")
            except Exception as db_err:
                logger.warning(f"Failed to load planner model from DB: {db_err}")

        # Fallback if no model found in DB
        if not planner_model:
            if settings.OPENAI_API_KEY:
                # Use gpt-3.5-turbo as safe default if global key exists
                planner_model = OpenAIChat(id="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY)
                logger.info("Planner using fallback OpenAI key")
            else:
                logger.error("No active model and no global OpenAI key found.")
                context.next_step = "execute" # Fail open to execution step
                return context

        planner = Agent(
            name="Workflow Planner",
            model=planner_model,
            instructions="""
            You are the Workflow Planner. Your job is to generate a detailed execution plan to complete the user's request.
            
            Available Operations:
            - retrieve: Retrieve documents from Knowledge Base. Use this if the user asks for information that might be in the docs.
            - execute: Execute the main agent logic (LLM/Tools). Use this for reasoning, calculation, or answering based on context.
            - persist: Save the result. Use this after execution is done.
            - finish: End the workflow.
            
            Rules:
            1. Return a valid JSON object matching the ExecutionPlan schema.
            2. Each step must have a unique sequence number (step_id).
            3. Specify dependencies if a step relies on the output of a previous one.
            4. Estimate time and resources.
            5. Do NOT include generic or irrelevant steps.
            6. If the task is simple, the plan can be short (e.g., just execute -> finish).
            7. Use keys: reasoning (string) and steps (array). Each step must include: step_id, operation, description, dependencies, estimated_time (seconds, number), required_resources (array of strings).
            8. Do not include markdown code blocks (```json). Just the raw JSON string.
            9. **CRITICAL**: The `description` and `reasoning` MUST be in Chinese (Simplified Chinese). The `description` should be a short, clear task name (e.g. "执行代码计算斐波那契数列", "检索关于React的文档").
            10. Break down complex tasks into multiple `execute` steps if needed, with clear descriptions for each phase.
            
            Current State:
            - User Message: {user_message}
            - History Length: {history_len}
            - Previous Steps: {step_history}
            
            Return the ExecutionPlan JSON.
            """,
            # response_model=ExecutionPlan, # Removed due to compatibility issues
            tools=[], # Explicitly disable tools to prevent hallucination issues
        )
        
        # Prepare context variables
        history_len = len(context.history) if context.history else 0
        step_history = context.meta.get("step_history", "None")

        run_response = await asyncio.to_thread(
            planner.run,
            f"User Message: {context.user_message}\nHistory Length: {history_len}\nPrevious Steps: {step_history}", 
            stream=False
        )
        
        # Manually parse JSON since response_model is not supported in init
        content_str = run_response.content
        
        # Check if content_str is an error message from Agno/LLM
        if "Failed to deserialize" in str(content_str) or not content_str:
            logger.error(f"Planner returned invalid content: {content_str}")
            # Fallback
            context.next_step = "execute"
            return context

        try:
            if isinstance(content_str, str):
                plan = _parse_execution_plan(content_str)
                logger.info(f"Planner generated {len(plan.steps)} steps. Reasoning: {plan.reasoning}")
                context.meta["current_plan"] = plan.model_dump()
                if plan.steps:
                    first_step = plan.steps[0]
                    context.next_step = first_step.operation
                else:
                    context.next_step = "finish"
            else:
                next_step = getattr(content_str, "next_step", None)
                if next_step:
                    context.next_step = next_step
                else:
                    context.next_step = "execute"
        except Exception as json_err:
            logger.error(f"Failed to parse Planner JSON: {json_err}. Content: {content_str}")
            context.next_step = "execute"

        return context

    except Exception as e:
        logger.error(f"Planning failed: {e}")
        context.next_step = "execute" # Fallback
        return context
