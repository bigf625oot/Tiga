import pytest
from app.services.agent.schemas.plan import JsonFixer, TaskPlanParser, TaskPlan
from app.services.agent.components.clarifier import ClarificationResult

def test_json_fixer_trailing_comma():
    raw = '{"name": "test",}'
    cleaned = JsonFixer.clean(raw)
    assert cleaned == '{"name": "test"}'

def test_json_fixer_single_quotes():
    raw = "{'name': 'test'}"
    cleaned = JsonFixer.clean(raw)
    assert '"name":' in cleaned

def test_json_fixer_python_constants():
    raw = '{"isValid": True, "value": None, "isFalse": False}'
    cleaned = JsonFixer.clean(raw)
    assert 'true' in cleaned
    assert 'null' in cleaned
    assert 'false' in cleaned

def test_json_fixer_control_chars():
    raw = '{"name": "test\x00"}'
    cleaned = JsonFixer.clean(raw)
    assert '\x00' not in cleaned

def test_json_fixer_mixed():
    raw = '{"list": [1, 2, 3,], "isValid": True,}'
    cleaned = JsonFixer.clean(raw)
    assert cleaned == '{"list": [1, 2, 3], "isValid": true}'

def test_task_plan_parser_valid():
    raw = '{"steps": [{"id": 1, "task": "do something", "tool_name": "coder", "dependencies": []}], "estimated_reasoning": "test"}'
    parser = TaskPlanParser(TaskPlan)
    plan = parser.parse(raw)
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "coder"

def test_task_plan_parser_markdown():
    raw = '```json\n{"steps": [{"id": 1, "task": "do something", "tool_name": "coder", "dependencies": []}], "estimated_reasoning": "test"}\n```'
    parser = TaskPlanParser(TaskPlan)
    plan = parser.parse(raw)
    assert len(plan.steps) == 1
    assert plan.steps[0].task == "do something"

def test_task_plan_parser_invalid_structure():
    raw = '{"steps": "not a list"}'
    parser = TaskPlanParser(TaskPlan)
    with pytest.raises(Exception):
        parser.parse(raw)

def test_clarification_result_schema_ambiguous():
    data = {
        "is_ambiguous": True,
        "clarification_question": "What do you mean?",
        "reasoning": "Because."
    }
    result = ClarificationResult.model_validate(data)
    assert result.is_ambiguous is True
    assert result.clarification_question == "What do you mean?"

def test_clarification_result_schema_clear():
    data = {
        "is_ambiguous": False,
        "clarification_question": None,
        "reasoning": "Clear."
    }
    result = ClarificationResult.model_validate(data)
    assert result.is_ambiguous is False
    assert result.clarification_question is None
