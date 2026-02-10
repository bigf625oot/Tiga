import types


class FakeMessage:
    def __init__(self, role="assistant", content="", reasoning_content=None, tool_calls=None):
        self.role = role
        self.content = content
        self.reasoning_content = reasoning_content
        self.tool_calls = tool_calls or []


class FakeToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.function = types.SimpleNamespace(name=name, arguments=arguments)


class FakeClient:
    def __init__(self, script):
        self.script = script
        self.ptr = 0
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

    def _create(self, model, messages, tools=None, extra_body=None):
        msg = self.script[self.ptr]
        self.ptr += 1
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def test_single_tool_call():
    from app.services.tool_runner import run_reasoning_tool_loop

    script = [
        FakeMessage(reasoning_content="thinking...", tool_calls=[FakeToolCall("id1", "echo", '{"text": "hello"}')]),
        FakeMessage(content="done"),
    ]
    client = FakeClient(script)
    tools = [{"type": "function", "function": {"name": "echo", "parameters": {"type": "object"}}}]
    res = run_reasoning_tool_loop(
        client=client,
        model_id="deepseek-reasoner",
        user_prompt="hi",
        tools=tools,
        tool_call_map={"echo": lambda text: {"text": text}},
        enable_thinking=True,
    )
    assert res["final_message"].content == "done"


def test_failed_tool_call():
    from app.services.agent.tools.runner import run_reasoning_tool_loop

    script = [FakeMessage(tool_calls=[FakeToolCall("id2", "missing", "{}")]), FakeMessage(content="answer")]
    client = FakeClient(script)
    tools = [{"type": "function", "function": {"name": "missing", "parameters": {"type": "object"}}}]
    res = run_reasoning_tool_loop(
        client=client,
        model_id="deepseek-reasoner",
        user_prompt="run",
        tools=tools,
        tool_call_map={},  # no tool provided
        enable_thinking=True,
    )
    assert res["final_message"].content == "answer"
