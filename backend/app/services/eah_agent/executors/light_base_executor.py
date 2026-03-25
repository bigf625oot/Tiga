import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, List

from app.models.llm_model import LLMModel
from app.services.eah_agent.schemas.intent import IntentResult
from app.services.eah_agent.components.memory_manager import DefaultMemoryManager

class LightBaseExecutor(ABC):
    """
    杞婚噺绾у熀绫?(Light Executor)銆?
    涓昏鐢ㄤ簬 Quick 妯″紡绛変笉闇€瑕佸鏉傝鍒掍笌鍙嶆€濈殑鍦烘櫙銆?
    鍙寘鍚渶鍩虹鐨勬ā鍨嬩緷璧栧拰璁板繂绠＄悊锛堜笂涓嬫枃鍔犺浇锛夛紝浠庤€屼繚璇佹瀬浣庣殑寤惰繜銆?
    """
    
    def __init__(
        self,
        llm_model: Optional[LLMModel] = None,
        memory_manager: Optional[DefaultMemoryManager] = None,
    ):
        self.llm_model = llm_model
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def execute(
        self,
        input_text: str,
        intent: IntentResult,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        鏍稿績鎵ц娴侊細鐢卞瓙绫诲疄鐜扮畝鍗曠殑 Prompt 缁勮銆佸崟娆?LLM 璋冪敤鍜屾祦寮忚緭鍑恒€?
        """
        pass

    async def _prepare_history(self, session_id: str, current_query: str = "") -> List[Dict[str, Any]]:
        """
        閫氱敤杈呭姪鏂规硶锛氶€氳繃 MemoryManager 鍔犺浇骞跺帇缂╁巻鍙叉秷鎭€?
        渚涘瓙绫诲湪鍑嗗鎵ц涓婁笅鏂囨椂澶嶇敤銆?
        """
        if self.memory_manager:
            try:
                return await self.memory_manager.get_compressed_context(session_id, current_query)
            except Exception as e:
                self.logger.warning(f"Failed to load history for session {session_id}: {e}")
        return []

    def _yield_error(self, message: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
        """
        閫氱敤杈呭姪鏂规硶锛氭牸寮忓寲閿欒杈撳嚭浜嬩欢銆?
        """
        err_msg = f"{message}: {str(exc)}" if exc else message
        self.logger.error(err_msg, exc_info=True if exc else False)
        return {"type": "error", "content": err_msg}

