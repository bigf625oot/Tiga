import pytest
import asyncio
from unittest.mock import MagicMock, patch, ANY
from app.services.sandbox.e2b_sandbox import E2BSandboxService

# --- Mocks ---

class MockExecutionResult:
    def __init__(self, stdout=None, stderr=None, results=None, error=None):
        self.logs = MagicMock()
        self.logs.stdout = stdout or []
        self.logs.stderr = stderr or []
        self.results = results or []
        self.error = error

class MockSandbox:
    def __init__(self, *args, **kwargs):
        self.id = "mock-sandbox-id"
        self.api_key = kwargs.get("api_key")
        self.files = MagicMock()
        self.commands = MagicMock()
        self.closed = False

    def run_code(self, code, on_stdout=None, on_stderr=None):
        # Simulate execution
        if "print" in code:
            if on_stdout:
                # Simulate ProcessMessage object
                msg = MagicMock()
                msg.line = "Hello World"
                on_stdout(msg)
            return MockExecutionResult(stdout=["Hello World"])
        
        if "error" in code:
            if on_stderr:
                msg = MagicMock()
                msg.line = "RuntimeError"
                on_stderr(msg)
            err = MagicMock()
            err.name = "RuntimeError"
            err.value = "Something went wrong"
            err.traceback = "Traceback..."
            return MockExecutionResult(stderr=["RuntimeError"], error=err)

        if "plot" in code:
            # Simulate chart result
            res = MagicMock()
            res.png = "base64_png_data"
            res.jpeg = None
            res.text = None
            return MockExecutionResult(results=[res])

        return MockExecutionResult()

    def close(self):
        self.closed = True

    @classmethod
    def connect(cls, sandbox_id, api_key=None):
        if sandbox_id == "invalid-id":
             raise Exception("Connection refused")
        instance = cls(api_key=api_key)
        instance.id = sandbox_id
        return instance

# --- Tests ---

@pytest.fixture
def sandbox_service():
    with patch("app.core.config.settings.E2B_API_KEY", "test-key"):
        service = E2BSandboxService()
        # Reset active sandboxes
        service._active_sandboxes = {}
        yield service

@pytest.mark.asyncio
async def test_svc_001_init_sandbox_no_session(sandbox_service):
    """SVC-001: Initialize sandbox (No Session ID)"""
    with patch("app.services.sandbox.e2b_sandbox.Sandbox", side_effect=MockSandbox) as MockSandboxClass:
        # Call _get_sandbox indirectly or directly? It is internal but we need to test it.
        # Actually execute calls _get_sandbox. Let's test _get_sandbox directly.
        sb = sandbox_service._get_sandbox()
        assert sb.id == "mock-sandbox-id"
        assert sb.api_key == "test-key"
        # verify new instance created
        MockSandboxClass.assert_called_once()

@pytest.mark.asyncio
async def test_svc_002_reuse_sandbox_session(sandbox_service):
    """SVC-002: Reuse sandbox (With Session ID)"""
    with patch("app.services.sandbox.e2b_sandbox.Sandbox", side_effect=MockSandbox) as MockSandboxClass:
        # 1. First call creates it
        sb1 = sandbox_service._get_sandbox(session_id="session-1")
        assert sb1.id == "mock-sandbox-id"
        assert sandbox_service._active_sandboxes["session-1"] == "mock-sandbox-id"
        
        # 2. Second call reuses it (via connect)
        # Mock connect
        MockSandboxClass.connect = MagicMock(return_value=MockSandbox(api_key="test-key"))
        
        sb2 = sandbox_service._get_sandbox(session_id="session-1")
        # verify connect called with stored ID
        MockSandboxClass.connect.assert_called_with("mock-sandbox-id", api_key="test-key")

@pytest.mark.asyncio
async def test_svc_003_execute_simple_code(sandbox_service):
    """SVC-003: Execute simple Python code"""
    with patch("app.services.sandbox.e2b_sandbox.Sandbox", side_effect=MockSandbox):
        result = await sandbox_service.execute("print('Hello')", session_id="session-1")
        
        assert result["status"] == "success"
        assert "Hello World" in result["content"]
        assert result["session_id"] == "session-1"

@pytest.mark.asyncio
async def test_svc_004_execute_chart(sandbox_service):
    """SVC-004: Execute code generating chart"""
    with patch("app.services.sandbox.e2b_sandbox.Sandbox", side_effect=MockSandbox):
        result = await sandbox_service.execute("plot()", session_id="session-1")
        
        assert result["status"] == "success"
        assert len(result["files"]) == 1
        assert result["files"][0]["type"] == "image/png"
        assert result["files"][0]["content"] == "base64_png_data"

@pytest.mark.asyncio
async def test_svc_005_execute_error(sandbox_service):
    """SVC-005: Execute code throwing exception"""
    with patch("app.services.sandbox.e2b_sandbox.Sandbox", side_effect=MockSandbox):
        result = await sandbox_service.execute("error", session_id="session-1")
        
        assert result["status"] == "error"
        assert "RuntimeError" in result["content"]

@pytest.mark.asyncio
async def test_svc_006_upload_file(sandbox_service):
    """SVC-006: Upload file to sandbox"""
    # Use return_value instead of side_effect to control the instance
    with patch("app.services.sandbox.e2b_sandbox.Sandbox") as MockSandboxClass:
        # We need to capture the instance to verify write call
        mock_instance = MockSandbox(api_key="test-key")
        MockSandboxClass.return_value = mock_instance
        
        await sandbox_service.upload_file("session-1", "test.txt", b"content")
        
        mock_instance.files.write.assert_called_with("test.txt", b"content")

@pytest.mark.asyncio
async def test_svc_007_download_file(sandbox_service):
    """SVC-007: Download file from sandbox"""
    with patch("app.services.sandbox.e2b_sandbox.Sandbox") as MockSandboxClass:
        mock_instance = MockSandbox(api_key="test-key")
        mock_instance.files.read.return_value = b"content"
        MockSandboxClass.return_value = mock_instance
        
        content = await sandbox_service.download_file("session-1", "test.txt")
        
        assert content == b"content"
        mock_instance.files.read.assert_called_with("test.txt", format="bytes")

@pytest.mark.asyncio
async def test_svc_008_service_unavailable(sandbox_service):
    """SVC-008: E2B Service unavailable (API Key missing)"""
    sandbox_service.api_key = None
    result = await sandbox_service.execute("print('Hello')")
    
    assert result["status"] == "error"
    assert "E2B_API_KEY is not set" in result["content"]
