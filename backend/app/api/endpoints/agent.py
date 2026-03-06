import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.openclaw.gateway.agent import agent_ws_manager

router = APIRouter()
logger = logging.getLogger("openclaw.api.agent")

@router.websocket("/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Agno Agent Control Plane.
    """
    try:
        agent_id = await agent_ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await agent_ws_manager.handle_message(agent_id, data)
        except WebSocketDisconnect as e:
            logger.info(f"Agent websocket disconnected: code={e.code}")
            agent_ws_manager.disconnect(agent_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            agent_ws_manager.disconnect(agent_id)
    except Exception as e:
        logger.error(f"Connection rejected: {e}")
        # Connection closed in connect()
