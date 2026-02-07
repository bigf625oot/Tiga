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
logger.setLevel(logging.ERROR)

class MCPClient:
    """
    MCP Client using asyncio and aiohttp for WebSocket connections.
    Implements persistent connection, auto-reconnect, heartbeat, and connection pooling.
    """
    def __init__(self, server_url: str, client_id: str = "default", max_concurrent: int = 10):
        self.server_url = server_url
        self.client_id = client_id
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._msg_queue: asyncio.Queue = asyncio.Queue()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_attempts = 0
        self._max_retries = 5
        self._pool_size = max_concurrent
        
        # Performance metrics
        self._request_count = 0
        self._start_time = time.time()

    async def connect(self):
        """Establish WebSocket connection with auto-reconnect."""
        if self._connected:
            return

        async with self._lock:
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
                    
                    logger.info("Connected to MCP Server")
                    return
                except Exception as e:
                    self._reconnect_attempts += 1
                    logger.error(f"Connection failed: {e}")
                    if self._reconnect_attempts >= self._max_retries:
                        raise ConnectionError(f"Failed to connect after {self._max_retries} attempts")
                    
                    # Exponential backoff with jitter
                    sleep_time = backoff * (1 + random.random())
                    await asyncio.sleep(sleep_time)
                    backoff *= 2

    async def disconnect(self):
        """Close connection and cleanup."""
        self._connected = False
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
                        # MCP Ping/Heartbeat format (assuming JSON-RPC ping or similar)
                        # Adjust based on actual MCP spec if different
                        ping_msg = {"jsonrpc": "2.0", "method": "ping", "id": int(time.time())}
                        await self._ws.send_json(ping_msg)
                    except Exception as e:
                        logger.error(f"Heartbeat failed: {e}")
                        # Trigger reconnect logic if needed
        except asyncio.CancelledError:
            pass

    async def _receive_loop(self):
        """Listen for messages."""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._msg_queue.put(data)
                    except json.JSONDecodeError:
                        logger.error("Received invalid JSON")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self._ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
        finally:
            self._connected = False

    async def send_request(self, method: str, params: Optional[Dict] = None, request_id: Any = None) -> None:
        """Send a request to the MCP server."""
        if not self._connected:
            await self.connect()

        async with self._semaphore:
            try:
                # Log the outgoing request
                logger.info(f"MCP SEND [{method}] ID={request_id}: {str(params)[:500]}")
                
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params or {},
                    "id": request_id or str(uuid.uuid4())
                }
                
                # Enforce 10s timeout for network I/O
                async with asyncio.timeout(10.0):
                    await self._ws.send_json(payload)
                    self._request_count += 1
            except asyncio.TimeoutError:
                logger.error("Send request timeout")
                raise
            except Exception as e:
                logger.error(f"Send request failed: {e}", exc_info=True)
                raise

    async def receive_response(self, timeout: float = 10.0) -> Dict:
        """Wait for a response."""
        try:
            async with asyncio.timeout(timeout):
                resp = await self._msg_queue.get()
                # Log the incoming response
                logger.info(f"MCP RECV: {str(resp)[:500]}")
                return resp
        except asyncio.TimeoutError:
            logger.error("Receive response timeout")
            raise
        except Exception as e:
            logger.error(f"Receive response failed: {e}")
            raise

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
            "duration": duration
        }

# Global connection pool manager (if needed)
class MCPConnectionPool:
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}

    def get_client(self, server_url: str) -> MCPClient:
        if server_url not in self.clients:
            self.clients[server_url] = MCPClient(server_url)
        return self.clients[server_url]

mcp_pool = MCPConnectionPool()
