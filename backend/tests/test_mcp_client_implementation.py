import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.mcp_client import MCPClient
import aiohttp

@pytest.mark.asyncio
async def test_connect_success():
    client = MCPClient("ws://test.local")
    
    mock_session = MagicMock(spec=aiohttp.ClientSession) # Use MagicMock for the session object itself
    mock_ws = AsyncMock(spec=aiohttp.ClientWebSocketResponse)
    
    # ws_connect should be an AsyncMock that returns mock_ws when awaited
    mock_session.ws_connect = AsyncMock(return_value=mock_ws)
    mock_session.close = AsyncMock()
    mock_ws.close = AsyncMock()

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await client.connect()
        assert client._connected
        assert client._ws == mock_ws
        
        await client.disconnect()
        assert not client._connected
        mock_ws.close.assert_called_once()

@pytest.mark.asyncio
async def test_reconnect_logic():
    client = MCPClient("ws://test.local")
    client._max_retries = 2
    
    mock_session = MagicMock()
    mock_ws = AsyncMock()
    
    # Side effect: First call raises, second returns mock_ws
    # We need to setup side_effect on the AsyncMock
    mock_session.ws_connect = AsyncMock(side_effect=[Exception("Fail"), mock_ws])
    mock_session.close = AsyncMock()

    with patch("aiohttp.ClientSession", return_value=mock_session):
        # We need to mock sleep to speed up test
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await client.connect()
            
            assert client._connected
            assert mock_session.ws_connect.call_count == 2
            mock_sleep.assert_called()

@pytest.mark.asyncio
async def test_send_request():
    client = MCPClient("ws://test.local")
    client._connected = True
    client._ws = AsyncMock()
    
    await client.send_request("test_method", {"p": 1})
    client._ws.send_json.assert_called_once()
    args = client._ws.send_json.call_args[0][0]
    assert args["method"] == "test_method"
    assert args["params"] == {"p": 1}

@pytest.mark.asyncio
async def test_receive_response():
    client = MCPClient("ws://test.local")
    await client._msg_queue.put({"result": "ok"})
    
    res = await client.receive_response(timeout=1)
    assert res == {"result": "ok"}
