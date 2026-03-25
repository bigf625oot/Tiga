import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger("eah.components.experience")

class DefaultExperienceStore:
    """
    默认的 ExperienceStore 实现。
    当前作为桩代码使用内存存储，实际应接入 LightRAG 或专门的向量数据库。
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self._experiences: List[Dict[str, Any]] = []

    async def save_experience(self, session_id: str, task_desc: str, experience_summary: str, is_success: bool) -> None:
        experience = {
            "session_id": session_id,
            "task_desc": task_desc,
            "summary": experience_summary,
            "is_success": is_success
        }
        self._experiences.append(experience)
        logger.info(f"Saved experience for task: {task_desc[:50]}...")

    async def retrieve_relevant_experience(self, task_desc: str, top_k: int = 3) -> List[Dict[str, Any]]:
        # TODO: Implement semantic search over experiences
        # 目前返回最近的经验作为占位
        return self._experiences[-top_k:] if self._experiences else []
