"""
Agent WebSocket Endpoint
前端接口：
- WebSocket 连接 `/agent`
- 发送 JSON 格式的消息
- 接收 JSON 格式的响应
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.openclaw.gateway.agent import agent_ws_manager

router = APIRouter()
logger = logging.getLogger("openclaw.api.agent")

@router.websocket("/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Agno Agent Control Plane.
    功能：
    - 与智能体进行实时交互
    - 支持创建、管理多个智能体会话
    - 提供实时的智能体响应和状态更新
    """
    try:
        agent_id = await agent_ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await agent_ws_manager.handle_message(agent_id, data)
        except WebSocketDisconnect as e:
            logger.info(f"Agent websocket disconnected: code={e.code}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            agent_ws_manager.disconnect(agent_id)
    except Exception as e:
        logger.error(f"Connection rejected: {e}")
