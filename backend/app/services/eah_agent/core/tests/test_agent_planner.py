"""
测试套件: app/services/eah_agent/core/agent_planner.py
覆盖需求:
  - REQ-CORRECT-1: 第一轮成功时不触发纠错
  - REQ-CORRECT-2: 第一轮失败 → 第二轮自动携带错误反馈重试
  - REQ-CORRECT-3: 连续两轮失败 → 第三轮再试
  - REQ-CORRECT-4: 三轮全部失败 → 抛出 PlanValidationError，包含轮次信息
  - REQ-CORRECT-5: _format_error_feedback 能把 PlanValidationError 转成可读文字
  - REQ-CORRECT-6: 错误反馈包含字段路径、原因、LLM 原始输出摘要和 Schema 提示
  - REQ-CORRECT-7: 第二轮 prompt 中包含 "SELF-CORRECTION ROUND 2" 标记
  - REQ-CORRECT-8: 持久化异常时回滚 DB，不被纠错逻辑吞掉
"""
import asyncio
import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.services.eah_agent.core.schema import (
    PlanValidationError,
    TaskPlan,
    TaskStep,
)
from app.services.eah_agent.core.agent_planner import PlannerAgent


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_valid_plan_json() -> str:
    return (
        '{"steps":[{"id":1,"task":"搜索数据","tool_name":"web_search","dependencies":[]},'
        '{"id":2,"task":"整理报告","tool_name":"formatter","dependencies":[1]}],'
        '"estimated_reasoning":"先搜再整理"}'
    )

def _make_mock_response(content: str):
    """构造 agno agent.arun 的模拟返回对象"""
    resp = MagicMock()
    resp.content = content
    return resp

def _make_db_mock():
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    db.add_all = MagicMock()
    return db


# ── REQ-CORRECT-1: 第一轮成功不触发纠错 ──────────────────────────────────────

class TestSelfCorrectionLoop:

    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        """REQ-CORRECT-1: 第一轮 LLM 返回合法 JSON，直接落库，arun 只调用一次"""
        db = _make_db_mock()
        planner = PlannerAgent(db=db)

        valid_json = _make_valid_plan_json()
        mock_agent = AsyncMock()
        mock_agent.arun = AsyncMock(return_value=_make_mock_response(valid_json))
        planner._agent = mock_agent

        with patch("app.services.eah_agent.core.agent_planner.PlannerAgent._persist_plan",
                   new_callable=AsyncMock, return_value="plan-001"):
            result = await planner.create_plan("sess-001", "分析销售数据")

        assert result == "plan-001"
        assert mock_agent.arun.call_count == 1  # 只调用一次

    # ── REQ-CORRECT-2: 第一轮失败，第二轮携带错误反馈 ─────────────────────────

    @pytest.mark.asyncio
    async def test_retries_on_first_failure_with_error_feedback(self):
        """REQ-CORRECT-2: 第一轮返回无效 JSON → 第二轮 prompt 含错误反馈和 SELF-CORRECTION ROUND 2"""
        db = _make_db_mock()
        planner = PlannerAgent(db=db)

        valid_json = _make_valid_plan_json()
        mock_agent = AsyncMock()
        mock_agent.arun = AsyncMock(side_effect=[
            _make_mock_response("这不是 JSON"),   # round 1: 失败
            _make_mock_response(valid_json),       # round 2: 成功
        ])
        planner._agent = mock_agent

        with patch("app.services.eah_agent.core.agent_planner.PlannerAgent._persist_plan",
                   new_callable=AsyncMock, return_value="plan-002"):
            result = await planner.create_plan("sess-002", "目标")

        assert result == "plan-002"
        assert mock_agent.arun.call_count == 2

        # 第二轮 prompt 应包含纠错标记
        second_call_prompt = mock_agent.arun.call_args_list[1][0][0]
        assert "SELF-CORRECTION ROUND 2" in second_call_prompt

    # ── REQ-CORRECT-3: 两轮失败，第三轮再试 ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_third_round_triggered_after_two_failures(self):
        """REQ-CORRECT-3: 前两轮均返回无效 JSON，第三轮收到合法 JSON 后成功"""
        db = _make_db_mock()
        planner = PlannerAgent(db=db)

        valid_json = _make_valid_plan_json()
        mock_agent = AsyncMock()
        mock_agent.arun = AsyncMock(side_effect=[
            _make_mock_response("invalid round 1"),
            _make_mock_response("invalid round 2"),
            _make_mock_response(valid_json),
        ])
        planner._agent = mock_agent

        with patch("app.services.eah_agent.core.agent_planner.PlannerAgent._persist_plan",
                   new_callable=AsyncMock, return_value="plan-003"):
            result = await planner.create_plan("sess-003", "目标")

        assert result == "plan-003"
        assert mock_agent.arun.call_count == 3

        third_prompt = mock_agent.arun.call_args_list[2][0][0]
        assert "SELF-CORRECTION ROUND 3" in third_prompt

    # ── REQ-CORRECT-4: 三轮全部失败 → 抛异常 ───────────────────────────���────

    @pytest.mark.asyncio
    async def test_raises_after_three_failures(self):
        """REQ-CORRECT-4: 三轮全部无效 → 抛出 PlanValidationError，包含轮次提示"""
        db = _make_db_mock()
        planner = PlannerAgent(db=db)

        mock_agent = AsyncMock()
        mock_agent.arun = AsyncMock(side_effect=[
            _make_mock_response("bad 1"),
            _make_mock_response("bad 2"),
            _make_mock_response("bad 3"),
        ])
        planner._agent = mock_agent

        with pytest.raises(PlanValidationError) as exc_info:
            await planner.create_plan("sess-fail", "无法规划的目标")

        assert mock_agent.arun.call_count == 3
        assert "3" in str(exc_info.value)  # 错误信息应提及轮次数

    # ── REQ-CORRECT-5: _format_error_feedback 可读性 ─────────────────────────

    def test_format_error_feedback_with_validation_error(self):
        """REQ-CORRECT-5: 应将 PlanValidationError 转为对 LLM 可读的纯文本"""
        error = PlanValidationError(
            message="Schema validation failed",
            errors=[
                {"path": "steps.0.id", "issue": "value is not a valid integer", "received": "abc"},
                {"path": "steps.0.task", "issue": "field required", "received": None},
            ]
        )
        feedback = PlannerAgent._format_error_feedback(error, '{"steps":[{"id":"abc"}]}')

        assert "steps.0.id" in feedback
        assert "steps.0.task" in feedback
        assert "value is not a valid integer" in feedback
        # 原始输出摘要应被包含
        assert '{"steps"' in feedback

    def test_format_error_feedback_with_generic_error(self):
        """REQ-CORRECT-5: 普通 Exception 也应被安全转换"""
        feedback = PlannerAgent._format_error_feedback(
            ValueError("unexpected token"), "some bad text"
        )
        assert "unexpected token" in feedback

    def test_format_error_feedback_with_none_error(self):
        """REQ-CORRECT-5: None 错误不应崩溃"""
        feedback = PlannerAgent._format_error_feedback(None, "raw output")
        assert isinstance(feedback, str)

    # ── REQ-CORRECT-6: 反馈包含字段路径 + Schema 提示 ─────────────────────────

    def test_feedback_contains_schema_reminder(self):
        """REQ-CORRECT-6: 反馈末尾应包含 Schema 格式提示，帮助 LLM 对齐格式"""
        feedback = PlannerAgent._format_error_feedback(
            PlanValidationError("x", errors=[]),
            "raw"
        )
        assert "steps" in feedback
        assert "estimated_reasoning" in feedback
        assert "tool_name" in feedback

    def test_feedback_clips_long_raw_output(self):
        """REQ-CORRECT-6: 超长 raw output 应被截断，防止 prompt 过长"""
        long_raw = "A" * 5000
        feedback = PlannerAgent._format_error_feedback(
            PlanValidationError("x", errors=[]),
            long_raw
        )
        # 反馈中 raw 部分不应超过 2000 字符（有 buffer）
        assert len(feedback) < 4000

    # ── REQ-CORRECT-7: 第二轮 prompt 格式验证 ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_correction_prompt_contains_original_goal(self):
        """REQ-CORRECT-7: 纠错 prompt 仍包含原始用户目标，不丢失上下文"""
        db = _make_db_mock()
        planner = PlannerAgent(db=db)

        valid_json = _make_valid_plan_json()
        mock_agent = AsyncMock()
        mock_agent.arun = AsyncMock(side_effect=[
            _make_mock_response("bad"),
            _make_mock_response(valid_json),
        ])
        planner._agent = mock_agent

        user_goal = "生成季度销售分析报告"
        with patch("app.services.eah_agent.core.agent_planner.PlannerAgent._persist_plan",
                   new_callable=AsyncMock, return_value="plan-x"):
            await planner.create_plan("sess", user_goal)

        second_prompt = mock_agent.arun.call_args_list[1][0][0]
        assert user_goal in second_prompt

    # ── REQ-CORRECT-8: 持久化失败时 DB 回滚 ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_db_rollback_on_persist_failure(self):
        """REQ-CORRECT-8: _persist_plan 抛出异常时必须调用 db.rollback()"""
        db = _make_db_mock()
        planner = PlannerAgent(db=db)

        valid_json = _make_valid_plan_json()
        mock_agent = AsyncMock()
        mock_agent.arun = AsyncMock(return_value=_make_mock_response(valid_json))
        planner._agent = mock_agent

        with patch("app.services.eah_agent.core.agent_planner.PlannerAgent._persist_plan",
                   new_callable=AsyncMock, side_effect=RuntimeError("DB 磁盘满")):
            with pytest.raises(RuntimeError, match="DB 磁盘满"):
                await planner.create_plan("sess-db-fail", "目标")

        db.rollback.assert_awaited_once()
        db.commit.assert_not_awaited()
