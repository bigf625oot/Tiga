import pytest

from app.services.eah_agent.core.schema import PlanValidationError, TaskPlan, parse_task_plan


def test_parse_task_plan_from_dict() -> None:
    plan = parse_task_plan(
        {
            "steps": [{"id": 1, "task": "t1", "tool_name": "tool", "dependencies": []}],
            "estimated_reasoning": "r",
        }
    )
    assert isinstance(plan, TaskPlan)
    assert plan.steps[0].id == 1


def test_parse_task_plan_from_json_string() -> None:
    plan = parse_task_plan(
        '{"steps":[{"id":1,"task":"t1","tool_name":"tool","dependencies":[]}],"estimated_reasoning":"r"}'
    )
    assert isinstance(plan, TaskPlan)
    assert plan.estimated_reasoning == "r"


def test_parse_task_plan_from_fenced_json() -> None:
    plan = parse_task_plan(
        "```json\n"
        '{"steps":[{"id":1,"task":"t1","tool_name":"tool","dependencies":[]}],"estimated_reasoning":"r"}\n'
        "```"
    )
    assert isinstance(plan, TaskPlan)
    assert plan.steps[0].tool_name == "tool"


def test_parse_task_plan_from_text_with_json_fragment() -> None:
    plan = parse_task_plan(
        "Here is the plan:\n"
        '{"steps":[{"id":1,"task":"t1","tool_name":"tool","dependencies":[]}],"estimated_reasoning":"r"}\n'
        "Thanks."
    )
    assert isinstance(plan, TaskPlan)
    assert plan.steps[0].task == "t1"

def test_parse_task_plan_accepts_trailing_commas() -> None:
    plan = parse_task_plan(
        '{"steps":[{"id":1,"task":"t1","tool_name":"tool","dependencies":[],},],"estimated_reasoning":"r",}'
    )
    assert plan.steps[0].id == 1


def test_parse_task_plan_rejects_non_json() -> None:
    with pytest.raises(PlanValidationError):
        parse_task_plan("not json")


def test_parse_task_plan_invalid_json_reports_parse_failure() -> None:
    with pytest.raises(PlanValidationError) as e:
        parse_task_plan('{"steps":[}')
    assert "parse/validate failed" in str(e.value) or "JSON" in str(e.value)
