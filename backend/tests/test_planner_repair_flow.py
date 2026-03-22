import pytest

from app.services.eah_agent.core.agent_planner import PlannerAgent


class _FakeBegin:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeDB:
    def begin_nested(self):
        return _FakeBegin()

    async def commit(self):
        return None

    async def rollback(self):
        return None


class _FakeResp:
    def __init__(self, content):
        self.content = content


class _FakeAgent:
    def __init__(self, outputs):
        self._outputs = list(outputs)

    async def arun(self, prompt):
        if not self._outputs:
            return _FakeResp("")
        return _FakeResp(self._outputs.pop(0))


@pytest.mark.asyncio
async def test_planner_repairs_non_json_plan_output(monkeypatch) -> None:
    db = _FakeDB()
    planner = PlannerAgent(db)  # type: ignore[arg-type]

    agent = _FakeAgent(
        outputs=[
            "我将把目标拆成若干步骤：先做A，再做B。",
            '{"steps":[{"id":1,"task":"A","tool_name":"tool","dependencies":[]}],"estimated_reasoning":"r"}',
        ]
    )

    async def _ensure_agent():
        return agent

    async def _persist_plan(session_id, user_goal, manifest):
        return "plan123"

    monkeypatch.setattr(planner, "_ensure_agent", _ensure_agent)
    monkeypatch.setattr(planner, "_persist_plan", _persist_plan)

    plan_id = await planner.create_plan("sid", "goal")
    assert plan_id == "plan123"
