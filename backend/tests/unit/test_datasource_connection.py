import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.strategies import get_strategy
from app.schemas.data_source import DataSourceTestResult
import asyncio
import asyncssh
import aiohttp
from sqlalchemy.exc import OperationalError, InterfaceError

@pytest.mark.asyncio
async def test_sftp_connection_success():
    config = {"host": "test", "username": "user", "password": "pw"}
    strategy = get_strategy("sftp", config)
    
    # Use MagicMock for connect because it returns an async context manager
    with patch("asyncssh.connect", new_callable=MagicMock) as mock_connect:
        mock_conn_ctx = MagicMock()
        mock_conn = MagicMock() # The connection object
        
        mock_connect.return_value = mock_conn_ctx
        mock_conn_ctx.__aenter__.return_value = mock_conn
        
        mock_sftp_ctx = MagicMock()
        mock_sftp = AsyncMock() # The sftp client object
        
        mock_conn.start_sftp_client.return_value = mock_sftp_ctx
        mock_sftp_ctx.__aenter__.return_value = mock_sftp
        
        # Mock listdir to return list of filenames
        mock_sftp.listdir.return_value = ["file1.txt", "file2.txt"]
        
        result = await strategy.test_connection()
        
        assert result["success"] is True, f"Failed with: {result.get('message')}"
        assert "file1.txt" in result["message"]

@pytest.mark.asyncio
async def test_sftp_connection_auth_fail():
    config = {"host": "test", "username": "user"}
    strategy = get_strategy("sftp", config)
    
    # Patch connect to raise PermissionDenied
    # Since connect is mocked as MagicMock, calling it raises the side_effect
    with patch("asyncssh.connect", side_effect=asyncssh.PermissionDenied("Auth failed")):
        result = await strategy.test_connection()
        assert result["success"] is False
        assert result["error_type"] == "AUTH_FAILED"

@pytest.mark.asyncio
async def test_sftp_connection_timeout():
    config = {"host": "test"}
    strategy = get_strategy("sftp", config)
    
    with patch("asyncssh.connect", side_effect=asyncio.TimeoutError):
        result = await strategy.test_connection()
        assert result["success"] is False
        assert result["error_type"] == "TIMEOUT"

@pytest.mark.asyncio
async def test_database_connection_success():
    config = {"type": "postgresql", "host": "localhost", "database": "db"}
    strategy = get_strategy("database", config)
    
    with patch("app.strategies.database.create_async_engine") as mock_engine_create:
        mock_engine = MagicMock() # Engine object
        mock_conn_ctx = MagicMock() # Context manager
        mock_conn = AsyncMock() # Connection object
        
        mock_engine_create.return_value = mock_engine
        
        # connect() returns context manager
        mock_engine.connect.return_value = mock_conn_ctx
        mock_conn_ctx.__aenter__.return_value = mock_conn
        
        # _get_engine is async? No, create_async_engine is sync function returning engine.
        # But _get_engine is async in strategy.
        # Wait, strategy._get_engine is async. It calls create_async_engine.
        # create_async_engine is sync.
        # So mocking create_async_engine return value is enough.
        
        result = await strategy.test_connection()
        
        assert result["success"] is True, f"Failed with: {result.get('message')}"
        mock_conn.execute.assert_called_once()

@pytest.mark.asyncio
async def test_database_connection_auth_fail():
    config = {"type": "postgresql"}
    strategy = get_strategy("database", config)
    
    with patch("app.strategies.database.create_async_engine") as mock_engine_create:
        mock_engine = MagicMock()
        mock_engine_create.return_value = mock_engine
        
        # Make connect raise OperationalError
        mock_engine.connect.side_effect = OperationalError("password authentication failed", params=None, orig=None)
        
        result = await strategy.test_connection()
        
        assert result["success"] is False
        # The strategy checks str(e).lower(). "password authentication failed" contains "password".
        assert result["error_type"] == "AUTH_FAILED", f"Got {result['error_type']} instead of AUTH_FAILED. Message: {result['message']}"

@pytest.mark.asyncio
async def test_crawler_connection_success():
    config = {"url": "https://example.com", "subtype": "other"}
    strategy = get_strategy("crawler", config)
    
    with patch("aiohttp.ClientSession.head") as mock_head:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_head.return_value.__aenter__.return_value = mock_resp
        
        result = await strategy.test_connection()
        assert result["success"] is True

@pytest.mark.asyncio
async def test_crawler_connection_tavily_fail():
    config = {"subtype": "tavily", "api_key": "invalid"}
    strategy = get_strategy("crawler", config)
    
    with patch("aiohttp.ClientSession.head") as mock_head:
        mock_resp = AsyncMock()
        mock_resp.status = 401
        mock_head.return_value.__aenter__.return_value = mock_resp
        
        result = await strategy.test_connection()
        assert result["success"] is False
        assert result["error_type"] == "INVALID_API_KEY"

@pytest.mark.asyncio
async def test_api_connection_success():
    config = {"url": "https://api.example.com", "method": "GET"}
    strategy = get_strategy("api", config)
    
    with patch("aiohttp.ClientSession.request") as mock_req:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.content.read.return_value = b"some data"
        mock_req.return_value.__aenter__.return_value = mock_resp
        
        result = await strategy.test_connection()
        assert result["success"] is True
        assert "some data" in result["message"]

@pytest.mark.asyncio
async def test_api_connection_server_error():
    config = {"url": "https://api.example.com"}
    strategy = get_strategy("api", config)
    
    with patch("aiohttp.ClientSession.request") as mock_req:
        mock_resp = AsyncMock()
        mock_resp.status = 503
        mock_resp.content.read.return_value = b"Service Unavailable"
        mock_req.return_value.__aenter__.return_value = mock_resp
        
        result = await strategy.test_connection()
        assert result["success"] is False
        assert result["error_type"] == "SERVER_ERROR"
