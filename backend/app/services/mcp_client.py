import asyncio
import logging
import json
import time
import random
import uuid
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import aiohttp

# Configure logging
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Let the app configure logging level

class MCPClient:
    """
    MCP Client using asyncio and aiohttp for WebSocket connections.
    Implements persistent connection, auto-reconnect, heartbeat, connection pooling,
    and robust request/response correlation.
    """
    def __init__(self, server_url: str, client_id: str = "default", max_concurrent: int = 10):
        self.server_url = server_url
        self.client_id = client_id
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # Request correlation: map request_id -> Future
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_attempts = 0
        self._max_retries = 5
        self._pool_size = max_concurrent
        
        # Context and Capabilities
        self._server_capabilities = {}
        self._client_capabilities = {
            "roots": {"listChanged": True},
            "sampling": {}
        }
        self._initialized = False
        
        # Performance metrics
        self._request_count = 0
        self._start_time = time.time()

    async def connect(self):
        """Establish WebSocket connection with auto-reconnect."""
        if self._connected:
            return

        async with self._lock:
            # Double check inside lock
            if self._connected:
                return

            if self._session is None:
                self._session = aiohttp.ClientSession()

            backoff = 1
            while self._reconnect_attempts < self._max_retries:
                try:
                    logger.info(f"Connecting to {self.server_url} (Attempt {self._reconnect_attempts + 1})")
                    self._ws = await self._session.ws_connect(self.server_url, timeout=10.0)
                    self._connected = True
                    self._reconnect_attempts = 0
                    
                    # Start background tasks
                    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    self._receive_task = asyncio.create_task(self._receive_loop())
                    
                    # Perform MCP Handshake
                    await self._initialize()
                    
                    logger.info("Connected to MCP Server")
                    return
                except Exception as e:
                    self._reconnect_attempts += 1
                    logger.error(f"Connection failed: {e}")
                    self._connected = False # Ensure flag is reset
                    if self._reconnect_attempts >= self._max_retries:
                        raise ConnectionError(f"Failed to connect after {self._max_retries} attempts")
                    
                    # Exponential backoff with jitter
                    sleep_time = backoff * (1 + random.random())
                    await asyncio.sleep(sleep_time)
                    backoff *= 2

    async def _initialize(self):
        """Perform MCP initialization handshake."""
        try:
            # Send initialize request
            response = await self.send_request("initialize", {
                "protocolVersion": "2024-11-05", # Use latest or negotiated version
                "capabilities": self._client_capabilities,
                "clientInfo": {"name": "tiga-backend", "version": "1.0.0"}
            })
            
            self._server_capabilities = response.get("capabilities", {})
            self._initialized = True
            
            # Send initialized notification
            await self.send_notification("notifications/initialized")
            logger.info(f"MCP Initialized. Server capabilities: {self._server_capabilities}")
            
        except Exception as e:
            logger.error(f"MCP Initialization failed: {e}")
            raise

    async def disconnect(self):
        """Close connection and cleanup."""
        self._connected = False
        self._initialized = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Cancel all pending requests
        for req_id, future in self._pending_requests.items():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

        if self._ws:
            await self._ws.close()
        
        if self._session:
            await self._session.close()
            self._session = None
            
        logger.info("Disconnected from MCP Server")

    async def _heartbeat_loop(self):
        """Send heartbeat every 30 seconds."""
        try:
            while self._connected:
                await asyncio.sleep(30)
                if self._ws and not self._ws.closed:
                    try:
                        # MCP Ping
                        await self.send_request("ping", timeout=5.0)
                    except Exception as e:
                        logger.warning(f"Heartbeat failed: {e}")
                        # Could trigger reconnect here if needed
        except asyncio.CancelledError:
            pass

    async def _receive_loop(self):
        """Listen for messages and dispatch to pending requests."""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        
                        # Handle Response
                        if "id" in data:
                            req_id = data["id"]
                            if req_id in self._pending_requests:
                                future = self._pending_requests.pop(req_id)
                                if not future.done():
                                    if "error" in data:
                                        future.set_exception(Exception(f"MCP Error: {data['error']}"))
                                    else:
                                        # JSON-RPC success result is in 'result'
                                        future.set_result(data.get("result"))
                            else:
                                # ID not found, might be a notification or timed out request
                                pass
                        else:
                            # Handle Notifications (method without id)
                            method = data.get("method")
                            if method:
                                logger.info(f"Received notification: {method}")
                                # TODO: Handle specific notifications if needed
                                
                    except json.JSONDecodeError:
                        logger.error("Received invalid JSON")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self._ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
        finally:
            self._connected = False
            self._initialized = False

    async def send_notification(self, method: str, params: Optional[Dict] = None) -> None:
        """Send a notification (no response expected)."""
        if not self._connected:
            await self.connect()
            
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        await self._ws.send_json(payload)

    async def send_request(self, method: str, params: Optional[Dict] = None, timeout: float = 20.0) -> Any:
        """Send a request to the MCP server and wait for response."""
        if not self._connected:
            await self.connect()

        async with self._semaphore:
            req_id = str(uuid.uuid4())
            future = asyncio.get_running_loop().create_future()
            self._pending_requests[req_id] = future
            
            try:
                # logger.debug(f"MCP SEND [{method}] ID={req_id}")
                
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params or {},
                    "id": req_id
                }
                
                await self._ws.send_json(payload)
                self._request_count += 1
                
                # Wait for response
                async with asyncio.timeout(timeout):
                    return await future
            except asyncio.TimeoutError:
                # Cleanup future if timed out
                if req_id in self._pending_requests:
                    self._pending_requests.pop(req_id)
                logger.error(f"Request {method} timed out")
                raise
            except Exception as e:
                if req_id in self._pending_requests:
                    self._pending_requests.pop(req_id)
                logger.error(f"Send request failed: {e}")
                raise

    async def list_tools(self) -> List[Dict]:
        """Fetch available tools."""
        response = await self.send_request("tools/list")
        return response.get("tools", [])

    async def call_tool(self, name: str, arguments: Dict) -> Any:
        """Call a specific tool."""
        response = await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        return response

    @asynccontextmanager
    async def session(self):
        """Async context manager for connection."""
        try:
            await self.connect()
            yield self
        finally:
            await self.disconnect()

    def get_metrics(self) -> Dict:
        """Return performance metrics."""
        duration = time.time() - self._start_time
        qps = self._request_count / duration if duration > 0 else 0
        return {
            "qps": qps,
            "requests": self._request_count,
            "duration": duration,
            "connected": self._connected,
            "pending_requests": len(self._pending_requests)
        }

# Global connection pool manager
class MCPConnectionPool:
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self._lock = asyncio.Lock()

    async def get_client(self, server_url: str) -> MCPClient:
        async with self._lock:
            if server_url not in self.clients:
                self.clients[server_url] = MCPClient(server_url)
            # Ensure connected? 
            # We can let the caller call connect() or do it here lazily.
            # Client.connect() is idempotent so it's safe.
            return self.clients[server_url]
    
    async def close_all(self):
        async with self._lock:
            for client in self.clients.values():
                await client.disconnect()
            self.clients.clear()

mcp_pool = MCPConnectionPool()
