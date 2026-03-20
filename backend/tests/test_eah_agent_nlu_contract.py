import importlib

import pytest


def test_import_agent_nlu_module():
    mod = importlib.import_module("app.services.eah_agent.core.agent_nlu")
    assert hasattr(mod, "IntentResult")


def test_intent_result_accepts_task_params_alias():
    from app.services.eah_agent.core.agent_nlu import IntentResult

    intent = IntentResult(
        intent="chat",
        confidence=0.42,
        reasoning="ok",
        task_params={"entities": ["a"], "locations": ["b"], "time_range": "2026"},
    )
    assert intent.parameters["entities"] == ["a"]
    assert intent.task_params["locations"] == ["b"]


@pytest.mark.asyncio
async def test_control_plane_forced_intent_has_reasoning():
    from app.services.eah_agent.core.agent_control_plane import AgnoControlPlane, OrchestrationContext

    cp = AgnoControlPlane(llm_model=None)
    ctx = OrchestrationContext(user_input="x", db=None, session_id="s", kwargs={"mode": "plan"})
    result = await cp._resolve_intent(ctx)
    assert result.intent.value == "task"
    assert isinstance(result.reasoning, str) and result.reasoning


@pytest.mark.asyncio
async def test_control_plane_exception_fallback_has_reasoning(monkeypatch):
    from app.services.eah_agent.core import agent_control_plane
    from app.services.eah_agent.core.agent_control_plane import AgnoControlPlane, OrchestrationContext

    async def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(agent_control_plane.NluService, "analyze", _boom, raising=True)

    cp = AgnoControlPlane(llm_model=None)
    ctx = OrchestrationContext(user_input="x", db=None, session_id="s", kwargs={})
    result = await cp._resolve_intent(ctx)
    assert result.intent.value == "chat"
    assert "fallback" in result.reasoning.lower()
