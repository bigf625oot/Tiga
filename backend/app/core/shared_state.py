from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import json
import time
from app.core.redis import get_redis_connection

class AgentConfig(BaseModel):
    model_id: str
    instructions: str
    tools: List[str] = []
    knowledge_base: Optional[Dict[str, Any]] = None

class SharedState(BaseModel):
    session_id: str
    mode: str
    agent_config: Optional[AgentConfig] = None
    temp_doc_ids: List[str] = []
    ui_state: Dict[str, Any] = {}
    updated_at: float = 0.0

class StateManager:
    _instance = None

    def __init__(self):
        self.redis = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get_redis(self):
        if not self.redis:
            self.redis = await get_redis_connection()
        return self.redis

    async def save_state(self, session_id: str, state: SharedState):
        redis = await self.get_redis()
        state.updated_at = time.time()
        await redis.set(f"shared_state:{session_id}", state.json(), ex=3600*24) # 24h TTL

    async def get_state(self, session_id: str) -> Optional[SharedState]:
        redis = await self.get_redis()
        data = await redis.get(f"shared_state:{session_id}")
        if data:
            return SharedState.parse_raw(data)
        return None

    async def update_mode(self, session_id: str, mode: str):
        state = await self.get_state(session_id)
        if state:
            state.mode = mode
            await self.save_state(session_id, state)
        else:
            # Create new state if not exists
            state = SharedState(session_id=session_id, mode=mode)
            await self.save_state(session_id, state)
