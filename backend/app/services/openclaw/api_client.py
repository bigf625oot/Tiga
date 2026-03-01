import httpx
import logging
import json
from typing import Any, Dict, Optional
from app.core.config import settings
 
logger = logging.getLogger("openclaw.http")
 
class OpenClawHttpClient:
    """
    OpenClaw HTTP 客户端（工具调用）。
    
    统一通过 /tools/invoke 调用所有工具，支持：
    - web_search / web_fetch
    - cron（增删改查）
    - message（发送消息）
    - 其他工具调用
    """
    
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None, timeout: float = 20.0):
        self.base_url = base_url or settings.OPENCLAW_BASE_URL
        if not self.base_url:
            logger.warning("OPENCLAW_BASE_URL 未配置，HTTP 客户端可能无法工作")
            
        # 自动修正 URL 格式
        if self.base_url:
            self.base_url = self.base_url.rstrip("/")
            if self.base_url.startswith("ws://"):
                self.base_url = self.base_url.replace("ws://", "http://", 1)
            elif self.base_url.startswith("wss://"):
                self.base_url = self.base_url.replace("wss://", "https://", 1)
                
        self.token = token or settings.OPENCLAW_GATEWAY_TOKEN or settings.OPENCLAW_TOKEN
        self.timeout = timeout
        
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            verify=False,
            follow_redirects=True
        )
 
    async def close(self):
        await self._client.aclose()
        
    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Agno-OpenClaw-Http/1.0"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
 
    async def invoke(self, tool: str, args: Dict[str, Any], session_key: Optional[str] = None) -> Dict[str, Any]:
        """
        调用 OpenClaw 工具接口 (POST /tools/invoke)
        
        Args:
            tool: 工具名称，如 "web_search", "cron", "message" 等
            args: 工具参数
            session_key: 会话标识（可选）
        
        Returns:
            {"ok": true/false, "result": {...} 或 "error": "..."}
        """
        if not self.base_url:
            return {"ok": False, "error": "OpenClaw Base URL not configured"}
 
        # 修正：使用统一的 /tools/invoke 端点
        url = f"{self.base_url}/tools/invoke"
        
        # 修正：请求体格式改为 { tool, args }
        payload = {
            "tool": tool,
            "args": args
        }
        
        # 可选：添加 sessionKey
        if session_key:
            payload["sessionKey"] = session_key
        
        try:
            logger.debug(f"HTTP Invoke: {tool} -> {url}")
            response = await self._client.post(url, json=payload, headers=self._headers())
            
            if 200 <= response.status_code < 300:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"ok": True, "raw": response.text}
            
            # 处理错误响应
            error_msg = f"HTTP {response.status_code}"
            try:
                err_data = response.json()
                if isinstance(err_data, dict):
                    error_msg = err_data.get("error") or err_data.get("message", error_msg)
            except:
                pass
                
            logger.error(f"OpenClaw HTTP 调用失败: {tool} - {error_msg}")
            return {"ok": False, "error": error_msg, "status": response.status_code}
            
        except httpx.RequestError as e:
            return {"ok": False, "error": f"Connection failed: {str(e)}"}
        except Exception as e:
            logger.error(f"OpenClaw 未知错误: {e}")
            return {"ok": False, "error": f"Unexpected error: {str(e)}"}
 
    # ── 便捷方法封装 ──────────────────────────────────────────────────────────
 
    async def web_search(self, query: str, count: int = 5) -> Dict[str, Any]:
        # 修正：使用 args 而不是 params
        return await self.invoke("web_search", {"query": query, "count": count})
 
    async def web_fetch(self, url: str, extract_mode: str = "markdown") -> Dict[str, Any]:
        return await self.invoke("web_fetch", {"url": url, "extractMode": extract_mode})
 
    async def cron_list(self) -> Dict[str, Any]:
        return await self.invoke("cron", {"action": "list"})
 
    async def cron_add(self, job_id: str, schedule: str, command: str) -> Dict[str, Any]:
        return await self.invoke("cron", {
            "action": "add",
            "id": job_id,
            "schedule": schedule,
            "command": command,
            "enabled": True
        })
 
    async def message_send(self, channel: str, content: str) -> Dict[str, Any]:
        return await self.invoke("message", {
            "action": "send",
            "channel": channel,
            "content": content
        })
 
    async def check_health(self) -> Dict[str, Any]:
        """
        检查 OpenClaw Gateway 健康状态
        
        端点: /health
        文档: [Development Channels Setup](5-development-channels-setup)
        """
        if not self.base_url:
             return {"available": False, "error": "URL not set"}
             
        try:
            # /health 端点存在
            url = f"{self.base_url}/health"
            resp = await self._client.get(url, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                return {"available": True, "data": data}
            
            return {"available": False, "status": resp.status_code}
        except Exception as e:
            return {"available": False, "error": str(e)}

    async def get_gateway_info(self) -> Dict[str, Any]:
        """
        获取 OpenClaw Gateway 详细信息
        尝试调用 /info 端点，如果失败则回退到 /health
        """
        if not self.base_url:
             return {"error": "URL not set"}
             
        try:
            # 尝试 /info
            url = f"{self.base_url}/info"
            resp = await self._client.get(url, timeout=3.0)
            if resp.status_code == 200:
                return resp.json()
                
            # 回退到 /health 并模拟 info 结构
            health = await self.check_health()
            if health.get("available"):
                data = health.get("data", {})
                return {
                    "version": data.get("version", "unknown"),
                    "gateway_url": self.base_url,
                    "websocket_url": None, # 无法从 health 推断
                    "status": "active"
                }
                
            return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}
 
    async def chat_completion(self, messages: list, model: str = "openclaw:main", stream: bool = True) -> Dict[str, Any]:
        """
        OpenAI 兼容的对话接口
        
        端点: /v1/chat/completions
        文档: [OpenAI HTTP处理](src/gateway/openai-http.ts)
        """
        if not self.base_url:
            return {"available": False, "error": "URL not set"}
        
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        try:
            response = await self._client.post(url, json=payload, headers=self._headers())
            return response.json()
        except Exception as e:
            return {"error": str(e)}