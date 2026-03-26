import asyncio
import sys
import types

import pytest

def _stub_pkg(name: str) -> None:
    if name in sys.modules:
        return
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m


def _stub_mod(name: str, **attrs) -> None:
    if name in sys.modules:
        return
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m


_stub_pkg("app.services.rag")
_stub_pkg("app.services.rag.retrieval")
_stub_pkg("app.services.rag.retrieval.engines")
if "app.services.rag.retrieval.engines.lightrag" not in sys.modules:
    m = types.ModuleType("app.services.rag.retrieval.engines.lightrag")
    m.lightrag_engine = object()
    sys.modules["app.services.rag.retrieval.engines.lightrag"] = m


class _StubHandler:
    def __init__(self, llm_model=None):
        self.llm_model = llm_model

    def process(self, *args, **kwargs):
        async def _gen():
            if False:
                yield None

        return _gen()


_stub_mod("app.services.agent.handlers.quick_handler", QuickHandler=_StubHandler)
_stub_mod("app.services.agent.handlers.plan_handler", PlanHandler=_StubHandler)
_stub_mod("app.services.agent.handlers.team_handler", TeamHandler=_StubHandler)
_stub_mod("app.services.agent.handlers.flow_handler", FlowHandler=_StubHandler)
_stub_mod("app.services.agent.handlers.data_handler", DataHandler=_StubHandler)

from app.services.agent.core.agent_control_plane import AgnoControlPlane, OrchestrationContext
from app.services.agent.core.agent_nlu import IntentResult, IntentType


@pytest.mark.asyncio
async def test_init_history_respects_persist_user_message_flag(monkeypatch) -> None:
    import app.services.agent.core.agent_control_plane as mod

    calls = []

    class _FakeHistory:
        def __init__(self, db):
            self.db = db

        async def ensure_session(self, *args, **kwargs):
            calls.append("ensure_session")

        async def add_message(self, *args, **kwargs):
            calls.append("add_message")

    monkeypatch.setattr(mod, "SessionHistory", _FakeHistory)

    cp = AgnoControlPlane()
    ctx = OrchestrationContext(user_input="hi", db=None, session_id="sid", kwargs={"persist_user_message": False})
    await cp._init_history(ctx)

    assert calls == ["ensure_session"]


@pytest.mark.asyncio
async def test_process_stream_respects_persist_assistant_message_flag(monkeypatch) -> None:
    import app.services.agent.core.agent_control_plane as mod

    class _DummyHandler:
        def process(self, augmented_input, intent, **kwargs):
            async def _gen():
                yield {"type": "content", "content": "ok"}

            return _gen()

    class _DummyAdapter:
        def __init__(self, extract_charts: bool = True):
            self.extract_charts = extract_charts

        async def to_standard_events(self, chunk):
            yield chunk

        async def flush(self):
            if False:
                yield None

    cp = AgnoControlPlane(llm_model=None)
    cp._handlers = {"chat": _DummyHandler()}

    async def _ensure_models(db):
        return None

    async def _resolve_intent(ctx):
        return IntentResult(intent=IntentType.CHAT, confidence=1.0, reasoning="r", parameters={})

    async def _fetch_knowledge(ctx):
        return ""

    async def _init_history(ctx):
        return None

    monkeypatch.setattr(cp, "_ensure_models", _ensure_models)
    monkeypatch.setattr(cp, "_resolve_intent", _resolve_intent)
    monkeypatch.setattr(cp, "_fetch_knowledge", _fetch_knowledge)
    monkeypatch.setattr(cp, "_init_history", _init_history)
    monkeypatch.setattr(mod, "AgnoStreamAdapter", _DummyAdapter)

    scheduled = {"finalize": 0}

    async def _finalize_session_safe(*args, **kwargs):
        scheduled["finalize"] += 1

    monkeypatch.setattr(cp, "_finalize_session_safe", _finalize_session_safe)

    real_create_task = asyncio.create_task

    def _spy_create_task(coro):
        name = getattr(getattr(coro, "cr_code", None), "co_name", "")
        if name == "_finalize_session_safe":
            scheduled["finalize"] += 10
        return real_create_task(coro)

    monkeypatch.setattr(mod.asyncio, "create_task", _spy_create_task)

    async for _ in cp.process_stream("hi", db=None, session_id="sid", persist_assistant_message=False):
        pass
    await asyncio.sleep(0)

    assert scheduled["finalize"] == 0
