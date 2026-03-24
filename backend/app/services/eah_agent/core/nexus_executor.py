"""
NexusExecutor
─────────────
Agno 执行引擎顶层编排器，职责：

1. 包装 UnifiedAgentWorkflow.run_stream()，将原始事件映射为标准 AgentEvent
2. 将每条事件写入 Redis Stream（stream:{agent_run_id}），支持断线续传
3. 暴露 stream() 异步生成器，供 FastAPI SSE 端点消费

事件映射（unified_workflow → AgentEvent）：
  type='plan'                              → plan_created
  type='task_started'                      → task_start(running)
  type='task_content'                      → thought
  type='task_tool_call' status=started     → tool_call
  type='task_tool_call' status=completed   → tool_output
  type='task_completed'                    → task_start(completed) + summary
  type='task_failed'                       → task_start(failed)
  type='artifacts'                         → artifact × N
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis_connection
from app.schemas.agent_event import (
    AgentEvent,
    ArtifactCard,
    ExecutionPlan,
    ToolCallInfo,
    ToolOutputInfo,
    TaskStartInfo,
    TaskStatus,
    TaskStep,
)
from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

logger = logging.getLogger("eah.nexus_executor")

_STREAM_MAXLEN = 10_000
_STREAM_TTL = 3600 * 24  # 24 小时


class NexusExecutor:
    """顶层执行引擎。"""

    def __init__(
        self,
        agent_run_id: str,
        session_id: str,
        db: AsyncSession,
        user_goal: str,
        images: Optional[List[str]] = None,
        resume_from: Optional[str] = None,
    ) -> None:
        self.agent_run_id = agent_run_id
        self.session_id = session_id
        self.db = db
        self.user_goal = user_goal
        self.images = images or []
        self.resume_from = resume_from
        self._start_ts = time.monotonic()

    async def stream(self) -> AsyncGenerator[AgentEvent, None]:
        redis = await get_redis_connection()
        stream_key = f"stream:{self.agent_run_id}"

        if self.resume_from:
            async for evt in self._replay_from_redis(redis, stream_key):
                yield evt
            return

        workflow = UnifiedAgentWorkflow(
            session_id=self.session_id,
            db=self.db,
            user_goal=self.user_goal,
            images=self.images,
        )

        current_task_id: Optional[str] = None

        async for raw in workflow.run_stream():
            events = list(self._map_event(raw, current_task_id))

            if raw.get("type") == "task_started":
                current_task_id = raw.get("task_id")
            elif raw.get("type") in ("task_completed", "task_failed"):
                current_task_id = None

            for evt in events:
                try:
                    await self._publish(redis, stream_key, evt)
                except Exception as exc:
                    logger.warning(f"[NexusExecutor] Redis publish failed: {exc}")
                yield evt

        try:
            await redis.expire(stream_key, _STREAM_TTL)
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────
    # 事件映射
    # ──────────────────────────────────────────────────────────────────────

    def _map_event(self, raw: Dict[str, Any], current_task_id: Optional[str]) -> List[AgentEvent]:
        t = raw.get("type", "")
        run_id = self.agent_run_id
        elapsed = int((time.monotonic() - self._start_ts) * 1000)

        # ── plan → plan_created ─────────────────���─────────────────────────
        if t == "plan":
            plan_data = raw.get("plan", {})
            plan = ExecutionPlan(
                plan_id=plan_data.get("id", run_id),
                reasoning=plan_data.get("reasoning", ""),
                tasks=[
                    TaskStep(
                        id=task.get("id", str(i)),
                        title=task.get("name", f"Task {i+1}"),
                        description=task.get("description", ""),
                        status=TaskStatus.pending,
                        assigned_role=task.get("assigned_agent_role", ""),
                    )
                    for i, task in enumerate(plan_data.get("tasks", []))
                ],
            )
            return [AgentEvent.plan_created(run_id, plan, elapsed_ms=elapsed)]

        # ── task_started → task_start(running) ───────────────────────────
        if t == "task_started":
            task_id = raw.get("task_id", "")
            return [
                AgentEvent.task_start(
                    run_id,
                    TaskStartInfo(
                        task_id=task_id,
                        title=raw.get("task_name", ""),
                        status=TaskStatus.running,
                    ),
                    elapsed_ms=elapsed,
                )
            ]

        # ── task_content → thought ────────────────────────────────────────
        if t == "task_content":
            content = raw.get("content", "")
            if not content:
                return []
            return [
                AgentEvent.thought(
                    run_id,
                    content,
                    task_id=raw.get("task_id") or current_task_id,
                    elapsed_ms=elapsed,
                )
            ]

        # ── task_tool_call → tool_call | tool_output ──────────────────────
        if t == "task_tool_call":
            tool_data = raw.get("tool", {})
            tool_name = tool_data.get("tool_name", "worker")
            status = tool_data.get("status", "started")
            tid = raw.get("task_id") or current_task_id

            if status == "started":
                return [
                    AgentEvent.tool_call(
                        run_id,
                        ToolCallInfo(tool=tool_name, args=tool_data.get("tool_args") or {}, task_id=tid),
                        elapsed_ms=elapsed,
                    )
                ]

            result = tool_data.get("result", "")
            logs: List[str] = []
            if isinstance(result, str) and result.strip():
                logs = [line for line in result.splitlines() if line.strip()]
            return [
                AgentEvent.tool_output(
                    run_id,
                    ToolOutputInfo(
                        tool=tool_name,
                        output=result,
                        logs=logs,
                        is_error=(status == "failed"),
                        task_id=tid,
                    ),
                    elapsed_ms=elapsed,
                )
            ]

        # ── task_completed → task_start(completed) + summary ─────────────
        if t == "task_completed":
            task_id = raw.get("task_id", "")
            result_summary = raw.get("result_summary", "")
            events: List[AgentEvent] = [
                AgentEvent.task_start(
                    run_id,
                    TaskStartInfo(task_id=task_id, status=TaskStatus.completed),
                    elapsed_ms=elapsed,
                )
            ]
            if result_summary:
                events.append(AgentEvent.summary(run_id, result_summary, task_id=task_id, elapsed_ms=elapsed))
            return events

        # ── task_failed → task_start(failed) ─────────────────────────────
        if t == "task_failed":
            task_id = raw.get("task_id", "")
            return [
                AgentEvent.task_start(
                    run_id,
                    TaskStartInfo(task_id=task_id, title=raw.get("error", ""), status=TaskStatus.failed),
                    elapsed_ms=elapsed,
                )
            ]

        # ── artifacts → artifact × N ──────────────────────────────────────
        if t == "artifacts":
            result_events: List[AgentEvent] = []
            for f in raw.get("files", []):
                try:
                    card = ArtifactCard.from_dict(f)
                    result_events.append(
                        AgentEvent.artifact(run_id, card, task_id=current_task_id, elapsed_ms=elapsed)
                    )
                except Exception as exc:
                    logger.warning(f"[NexusExecutor] Bad artifact dict {f}: {exc}")
            return result_events

        return []

    # ──────────────────────────────────────────────────────────────────────
    # Redis 操作
    # ──────────────────────────────────────────────────────────────────────

    async def _publish(self, redis: Any, stream_key: str, evt: AgentEvent) -> None:
        await redis.xadd(
            stream_key,
            {"data": evt.model_dump_json()},
            maxlen=_STREAM_MAXLEN,
            approximate=True,
        )

    async def _replay_from_redis(self, redis: Any, stream_key: str) -> AsyncGenerator[AgentEvent, None]:
        start_id = self.resume_from or "0-0"
        try:
            entries = await redis.xread({stream_key: start_id}, count=_STREAM_MAXLEN, block=0)
        except Exception as exc:
            logger.warning(f"[NexusExecutor] Redis replay failed: {exc}")
            return

        for _key, messages in entries:
            for _msg_id, fields in messages:
                raw_data = fields.get("data", "{}")
                try:
                    evt = AgentEvent.model_validate_json(raw_data)
                    yield evt
                except Exception as exc:
                    logger.warning(f"[NexusExecutor] Replay parse error: {exc}")
