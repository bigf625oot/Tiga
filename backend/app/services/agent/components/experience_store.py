import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import ChatMessage

logger = logging.getLogger("eah.components.experience")


@dataclass(slots=True)
class ExperienceRecord:
    session_id: str
    task_desc: str
    summary: str
    is_success: bool
    created_at: Any

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "task_desc": self.task_desc,
            "summary": self.summary,
            "is_success": self.is_success,
            "created_at": self.created_at,
        }


class DefaultExperienceStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_experience(
        self,
        session_id: str,
        task_desc: str,
        experience_summary: str,
        is_success: bool,
    ) -> None:
        msg = ChatMessage(
            session_id=session_id,
            role="system",
            content=experience_summary,
            message_type="experience",
            meta_data={
                "schema": "eah.experience.v1",
                "task_desc": task_desc,
                "is_success": bool(is_success),
            },
        )
        self.db.add(msg)
        await self.db.flush()  # Why: 依赖外层 Executor 的事务边界，避免 commit 导致并发读取到中间状态 (脏读)
        logger.info("experience_saved session_id=%s is_success=%s", session_id, bool(is_success))

    async def retrieve_relevant_experience(
        self,
        task_desc: str,
        top_k: int = 3,
        *,
        session_id: Optional[str] = None,
        candidate_window: int = 200,
    ) -> List[Dict[str, Any]]:
        if top_k <= 0:
            return []

        stmt = select(ChatMessage).where(ChatMessage.message_type == "experience")
        if session_id:
            stmt = stmt.where(ChatMessage.session_id == session_id)

        stmt = stmt.order_by(desc(ChatMessage.created_at)).limit(max(candidate_window, top_k))
        result = await self.db.execute(stmt)
        msgs = list(result.scalars().all())
        if not msgs:
            return []

        scored: List[Tuple[float, ExperienceRecord]] = []
        for m in msgs:
            meta = m.meta_data or {}
            record = ExperienceRecord(
                session_id=m.session_id,
                task_desc=str(meta.get("task_desc") or ""),
                summary=str(m.content or ""),
                is_success=bool(meta.get("is_success")),
                created_at=m.created_at,
            )
            scored.append((self._score(task_desc, record.task_desc), record))

        scored.sort(key=lambda x: (x[0], x[1].created_at), reverse=True)
        return [r.to_dict() for _, r in scored[:top_k]]

    def _score(self, query: str, candidate: str) -> float:
        q = self._tokens(query)
        c = self._tokens(candidate)
        if not q or not c:
            return 0.0
        inter = len(q.intersection(c))
        return inter / (len(q) ** 0.5)

    def _tokens(self, s: str) -> Set[str]:
        parts = self._tokenize(s)
        out: Set[str] = set()
        for p in parts:
            if not p:
                continue
            if self._looks_like_cjk_run(p) and len(p) >= 4:
                out.update(p)
            else:
                out.add(p.lower())
        return out

    def _tokenize(self, s: str) -> Iterable[str]:
        return re.findall(r"[\w\u4e00-\u9fff]+", s)

    def _looks_like_cjk_run(self, s: str) -> bool:
        return any("\u4e00" <= ch <= "\u9fff" for ch in s)
