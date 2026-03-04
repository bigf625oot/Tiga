from app.services.openclaw.gateway.service import OpenClawService


def test_normalize_ws_url_from_http():
    actual = OpenClawService._normalize_ws_url("http://127.0.0.1:18789")
    assert actual == "ws://127.0.0.1:18789/v1/agent"


def test_normalize_ws_url_keep_agent_path():
    actual = OpenClawService._normalize_ws_url("ws://127.0.0.1:18789/v1/agent")
    assert actual == "ws://127.0.0.1:18789/v1/agent"


def test_derive_gateway_url_from_ws():
    actual = OpenClawService._derive_gateway_url_from_ws("ws://127.0.0.1:18789/v1/agent")
    assert actual == "http://127.0.0.1:18789"
