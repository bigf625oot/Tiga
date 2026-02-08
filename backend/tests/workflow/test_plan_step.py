import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from app.workflow.steps.plan_step import plan_step, ExecutionPlan, PlanStepItem
from app.workflow.context import AgentContext

@pytest.fixture
def mock_context():
    return AgentContext(session_id="test_session", user_message="test message")

@pytest.fixture
def mock_db_session():
    with patch("app.workflow.steps.plan_step.AsyncSessionLocal") as MockSession:
        mock_session = AsyncMock()
        MockSession.return_value.__aenter__.return_value = mock_session
        
        # Setup default successful query result
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        # Mock active model
        mock_model = MagicMock()
        mock_model.model_id = "test-model"
        mock_model.api_key = "test-key"
        mock_model.base_url = "http://test"
        mock_model.provider = "openai"
        mock_scalars.first.return_value = mock_model
        
        mock_session.execute.return_value = mock_result
        
        yield mock_session

@pytest.fixture
def mock_planner_run(mock_db_session): # Add dependency on mock_db_session
    with patch("app.workflow.steps.plan_step.Agent") as MockAgent:
        # Create a mock instance
        mock_instance = MockAgent.return_value
        # Mock the run method
        mock_instance.run = MagicMock()
        yield mock_instance.run

@pytest.mark.asyncio
async def test_plan_step_single_step(mock_context, mock_planner_run):
    # Mock response
    plan = ExecutionPlan(
        reasoning="Simple task",
        steps=[
            PlanStepItem(step_id=1, operation="execute", description="Run logic", estimated_time=1.0, required_resources=[])
        ]
    )
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())

    result_context = await plan_step(mock_context)
    
    assert result_context.next_step == "execute"
    assert result_context.meta["current_plan"]["steps"][0]["operation"] == "execute"

@pytest.mark.asyncio
async def test_plan_step_multi_step(mock_context, mock_planner_run):
    plan = ExecutionPlan(
        reasoning="Complex task",
        steps=[
            PlanStepItem(step_id=1, operation="retrieve", description="Search docs", estimated_time=2.0, required_resources=["kb"]),
            PlanStepItem(step_id=2, operation="execute", description="Answer", dependencies=[1], estimated_time=1.0, required_resources=[])
        ]
    )
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())

    result_context = await plan_step(mock_context)
    
    assert result_context.next_step == "retrieve"
    assert len(result_context.meta["current_plan"]["steps"]) == 2

@pytest.mark.asyncio
async def test_plan_step_empty(mock_context, mock_planner_run):
    plan = ExecutionPlan(reasoning="Nothing to do", steps=[])
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())

    result_context = await plan_step(mock_context)
    
    assert result_context.next_step == "finish"

@pytest.mark.asyncio
async def test_plan_step_exception(mock_context, mock_planner_run):
    # Mock exception during run
    mock_planner_run.side_effect = Exception("LLM Error")

    result_context = await plan_step(mock_context)
    
    # Should fallback to execute
    assert result_context.next_step == "execute"

@pytest.mark.asyncio
async def test_plan_step_resources(mock_context, mock_planner_run):
    plan = ExecutionPlan(
        reasoning="Resource check",
        steps=[
            PlanStepItem(step_id=1, operation="execute", description="GPU task", estimated_time=10.0, required_resources=["GPU"])
        ]
    )
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())

    result_context = await plan_step(mock_context)
    
    steps = result_context.meta["current_plan"]["steps"]
    assert steps[0]["required_resources"] == ["GPU"]
    assert steps[0]["estimated_time"] == 10.0

@pytest.mark.asyncio
async def test_plan_step_dependencies(mock_context, mock_planner_run):
    plan = ExecutionPlan(
        reasoning="Dependency check",
        steps=[
            PlanStepItem(step_id=1, operation="retrieve", description="A", estimated_time=1.0),
            PlanStepItem(step_id=2, operation="execute", description="B", dependencies=[1], estimated_time=1.0)
        ]
    )
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())

    result_context = await plan_step(mock_context)
    steps = result_context.meta["current_plan"]["steps"]
    assert steps[1]["dependencies"] == [1]

# Add more cases as needed to reach 10
@pytest.mark.asyncio
async def test_plan_step_long_sequence(mock_context, mock_planner_run):
    steps = [
        PlanStepItem(step_id=i, operation="execute", description=f"Step {i}", estimated_time=0.5)
        for i in range(1, 11)
    ]
    plan = ExecutionPlan(reasoning="Long task", steps=steps)
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())

    result_context = await plan_step(mock_context)
    assert len(result_context.meta["current_plan"]["steps"]) == 10
    assert result_context.next_step == "execute"

@pytest.mark.asyncio
async def test_plan_step_persist(mock_context, mock_planner_run):
    plan = ExecutionPlan(
        reasoning="Save data",
        steps=[PlanStepItem(step_id=1, operation="persist", description="Save", estimated_time=0.1)]
    )
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())
    result_context = await plan_step(mock_context)
    assert result_context.next_step == "persist"

@pytest.mark.asyncio
async def test_plan_step_finish_explicit(mock_context, mock_planner_run):
    plan = ExecutionPlan(
        reasoning="Done",
        steps=[PlanStepItem(step_id=1, operation="finish", description="End", estimated_time=0)]
    )
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())
    result_context = await plan_step(mock_context)
    assert result_context.next_step == "finish"

@pytest.mark.asyncio
async def test_plan_step_accepts_time_estimate_and_missing_reasoning(mock_context, mock_planner_run):
    raw_plan = {
        "steps": [
            {
                "step_id": 1,
                "operation": "execute",
                "description": "Run",
                "dependencies": [],
                "time_estimate": "10s",
                "resource_estimate": "low",
            }
        ]
    }
    mock_planner_run.return_value = MagicMock(content=json.dumps(raw_plan))
    result_context = await plan_step(mock_context)
    assert result_context.next_step == "execute"
    steps = result_context.meta["current_plan"]["steps"]
    assert steps[0]["estimated_time"] == 10.0
    assert result_context.meta["current_plan"]["reasoning"] == ""

@pytest.mark.asyncio
async def test_plan_step_accepts_root_list(mock_context, mock_planner_run):
    raw_plan = [
        {
            "step_id": 1,
            "operation": "retrieve",
            "description": "Search docs",
            "dependencies": [],
            "time_estimate": "2s",
        }
    ]
    mock_planner_run.return_value = MagicMock(content=json.dumps(raw_plan))
    result_context = await plan_step(mock_context)
    assert result_context.next_step == "retrieve"
    assert result_context.meta["current_plan"]["reasoning"] == ""

@pytest.fixture
def mock_model_factory():
    with patch("app.workflow.steps.plan_step.ModelFactory") as MockFactory:
        yield MockFactory

@pytest.mark.asyncio
async def test_plan_step_with_agent_config(mock_context, mock_planner_run, mock_db_session, mock_model_factory):
    # Setup context
    mock_context.agent_id = "agent-123"
    
    # Mock DB responses
    # 1. Agent query result
    mock_agent = MagicMock()
    mock_agent.id = "agent-123"
    mock_agent.model_config = {"model_id": "special-model"}
    
    # 2. LLMModel query result
    mock_llm = MagicMock()
    mock_llm.model_id = "special-model"
    mock_llm.provider = "openai"
    
    # Get the scalars mock
    mock_scalars = mock_db_session.execute.return_value.scalars.return_value
    # Set side_effect: First call returns Agent, Second call returns LLMModel
    mock_scalars.first.side_effect = [mock_agent, mock_llm]
    
    # Mock Planner run
    plan = ExecutionPlan(reasoning="Agent task", steps=[])
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())
    
    await plan_step(mock_context)
    
    # Verify ModelFactory.create_model was called with the special LLM model
    mock_model_factory.create_model.assert_called_with(mock_llm)

@pytest.mark.asyncio
async def test_plan_step_fallback_to_active(mock_context, mock_planner_run, mock_db_session, mock_model_factory):
    # No agent_id in context
    mock_context.agent_id = None
    
    # Mock DB response: Active Model
    mock_active_model = MagicMock()
    mock_active_model.model_id = "active-model"
    
    mock_scalars = mock_db_session.execute.return_value.scalars.return_value
    mock_scalars.first.side_effect = [mock_active_model]
    
    # Mock Planner run
    plan = ExecutionPlan(reasoning="Active task", steps=[])
    mock_planner_run.return_value = MagicMock(content=plan.model_dump_json())
    
    await plan_step(mock_context)
    
    # Verify ModelFactory.create_model was called with active model
    mock_model_factory.create_model.assert_called_with(mock_active_model)
