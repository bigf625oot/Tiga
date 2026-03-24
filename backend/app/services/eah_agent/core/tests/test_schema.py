"""
测试套件: app/services/eah_agent/core/schema.py
覆盖需求:
  - REQ-SCHEMA-1: TaskStep / TaskPlan 强类型业务模型校验
  - REQ-SCHEMA-2: JsonFixer 自愈能力（Python 常量、单引号 key、多余逗号、控制字符）
  - REQ-SCHEMA-3: TaskPlanParser 启发式提取 + 深度验证
  - REQ-SCHEMA-4: parse_task_plan 兜底抛出 PlanValidationError
  - REQ-SCHEMA-5: ExecutionTaskStep 四态状态机 + output_logs
  - REQ-SCHEMA-6: ExecutionPlan 进度计算 + task 查找
"""
import pytest
from datetime import datetime

from app.services.eah_agent.core.schema import (
    # 规划阶段
    TaskStep,
    TaskPlan,
    JsonFixer,
    TaskPlanParser,
    PlanError,
    PlanParseError,
    PlanValidationError,
    parse_task_plan,
    # 运行时阶段
    RuntimeTaskStatus,
    ExecutionTaskStep,
    ExecutionPlan,
)


# ─────────────────────────────────────────────
# REQ-SCHEMA-1: 强类型业务模型
# ─────────────────────────────────────────────

class TestTaskStep:
    def test_valid_step_creation(self):
        step = TaskStep(id=1, task="分析数据", tool_name="python_executor", dependencies=[])
        assert step.id == 1
        assert step.task == "分析数据"
        assert step.tool_name == "python_executor"
        assert step.dependencies == []

    def test_step_with_dependencies(self):
        step = TaskStep(id=3, task="汇总报告", tool_name="report_tool", dependencies=[1, 2])
        assert step.dependencies == [1, 2]

    def test_step_rejects_empty_task(self):
        with pytest.raises(Exception):
            TaskStep(id=1, task="", tool_name="tool", dependencies=[])

    def test_step_ignores_extra_fields(self):
        """extra='ignore' 配置：多余字段不应抛出异常"""
        step = TaskStep(id=1, task="任务", tool_name="tool", dependencies=[], unknown_field="x")
        assert not hasattr(step, "unknown_field")

    def test_step_is_frozen(self):
        """frozen=True 配置：赋值应抛出异常"""
        step = TaskStep(id=1, task="任务", tool_name="tool", dependencies=[])
        with pytest.raises(Exception):
            step.task = "修改"  # type: ignore


class TestTaskPlan:
    def test_valid_plan(self):
        raw = {
            "steps": [
                {"id": 1, "task": "搜索", "tool_name": "web_search", "dependencies": []},
                {"id": 2, "task": "整理", "tool_name": "formatter", "dependencies": [1]},
            ],
            "estimated_reasoning": "先搜后整理",
        }
        plan = TaskPlan.model_validate(raw)
        assert len(plan.steps) == 2
        assert plan.estimated_reasoning == "先搜后整理"
        assert plan.version == "v1"  # default

    def test_plan_missing_steps_raises(self):
        with pytest.raises(Exception):
            TaskPlan.model_validate({"estimated_reasoning": "无步骤"})

    def test_plan_default_empty_reasoning(self):
        plan = TaskPlan.model_validate({
            "steps": [{"id": 1, "task": "t", "tool_name": "t", "dependencies": []}]
        })
        assert plan.estimated_reasoning == ""


# ─────────────────────────────────────────────
# REQ-SCHEMA-2: JsonFixer 自愈能力
# ────────��────────────────────────────────────

class TestJsonFixer:
    def test_removes_control_characters(self):
        dirty = '{"key": "val\x00ue"}'
        clean = JsonFixer.clean(dirty)
        assert "\x00" not in clean

    def test_fixes_python_true_false_none(self):
        dirty = '{"a": True, "b": False, "c": None}'
        clean = JsonFixer.clean(dirty)
        assert "true" in clean
        assert "false" in clean
        assert "null" in clean
        assert "True" not in clean

    def test_fixes_single_quote_keys(self):
        dirty = "{'steps': [], 'estimated_reasoning': 'ok'}"
        clean = JsonFixer.clean(dirty)
        # 单引号 key 应被替换
        assert '"steps"' in clean

    def test_removes_trailing_comma_in_object(self):
        dirty = '{"a": 1, "b": 2,}'
        clean = JsonFixer.clean(dirty)
        import json
        obj = json.loads(clean)
        assert obj["a"] == 1

    def test_removes_trailing_comma_in_array(self):
        dirty = '[1, 2, 3,]'
        clean = JsonFixer.clean(dirty)
        import json
        arr = json.loads(clean)
        assert arr == [1, 2, 3]

    def test_strips_whitespace(self):
        assert JsonFixer.clean("  hello  ") == "hello"


# ─────────────────────────────────────────────
# REQ-SCHEMA-3: TaskPlanParser 启发式解析
# ─────────────────────────────────────────────

VALID_JSON = '{"steps":[{"id":1,"task":"采集数据","tool_name":"scraper","dependencies":[]}],"estimated_reasoning":"先采集"}'

class TestTaskPlanParser:
    def setup_method(self):
        self.parser = TaskPlanParser(TaskPlan)

    def test_parses_clean_json_string(self):
        plan = self.parser.parse(VALID_JSON)
        assert len(plan.steps) == 1
        assert plan.steps[0].task == "采集数据"

    def test_parses_json_with_markdown_fence(self):
        fenced = f"```json\n{VALID_JSON}\n```"
        plan = self.parser.parse(fenced)
        assert plan.steps[0].tool_name == "scraper"

    def test_parses_json_with_leading_text(self):
        """LLM 常在 JSON 前后加解释文字"""
        noisy = f"当然，以下是规划：\n{VALID_JSON}\n希望对你有帮助。"
        plan = self.parser.parse(noisy)
        assert len(plan.steps) == 1

    def test_parses_dict_directly(self):
        d = {"steps": [{"id": 1, "task": "t", "tool_name": "t", "dependencies": []}], "estimated_reasoning": ""}
        plan = self.parser.parse(d)
        assert isinstance(plan, TaskPlan)

    def test_returns_existing_model_unchanged(self):
        original = TaskPlan.model_validate(
            {"steps": [{"id": 1, "task": "t", "tool_name": "t", "dependencies": []}]}
        )
        result = self.parser.parse(original)
        assert result is original

    def test_raises_parse_error_on_gibberish(self):
        with pytest.raises((PlanParseError, PlanValidationError)):
            self.parser.parse("这根本不是 JSON")

    def test_raises_validation_error_on_schema_mismatch(self):
        """JSON 合法但缺少 steps 字段"""
        with pytest.raises(PlanValidationError) as exc_info:
            self.parser.parse('{"estimated_reasoning": "无 steps"}')
        assert exc_info.value.validation_details  # 应有字段级错误详情

    def test_validation_error_contains_field_path(self):
        """错误应精确到 field path，便于 Self-Correction 反馈"""
        bad = '{"steps": [{"id": "not_int", "tool_name": "t", "dependencies": []}]}'
        with pytest.raises(PlanValidationError) as exc_info:
            self.parser.parse(bad)
        paths = [e["path"] for e in exc_info.value.validation_details]
        # 至少应包含指向 steps 数组某字段的路径
        assert any("steps" in p for p in paths)


# ─────────────────────────────────────────────
# REQ-SCHEMA-4: parse_task_plan 兜底转换
# ─────────────────────────────────────────────

class TestParseTaskPlan:
    def test_valid_input_returns_plan(self):
        plan = parse_task_plan(VALID_JSON)
        assert isinstance(plan, TaskPlan)

    def test_invalid_input_raises_plan_validation_error(self):
        with pytest.raises(PlanValidationError):
            parse_task_plan("完全无效的内容 @!#")

    def test_non_string_non_dict_raises(self):
        with pytest.raises(PlanValidationError):
            parse_task_plan(12345)

    def test_python_bool_fixed_automatically(self):
        """JsonFixer 应在 parse 前修复 Python 布尔值"""
        py_style = '{"steps":[{"id":1,"task":"t","tool_name":"t","dependencies":[]}],"estimated_reasoning":"ok","flag":True}'
        plan = parse_task_plan(py_style)
        assert len(plan.steps) == 1


# ─────────────────────────────────────────────
# REQ-SCHEMA-5: ExecutionTaskStep 四态状态机
# ─────────────────────────────────────────────

class TestExecutionTaskStep:
    def _make_step(self, **kw) -> ExecutionTaskStep:
        defaults = dict(task_id="t1", title="测试任务", description="执行测试")
        defaults.update(kw)
        return ExecutionTaskStep(**defaults)

    def test_default_status_is_pending(self):
        step = self._make_step()
        assert step.status == RuntimeTaskStatus.pending

    def test_mark_running_sets_status_and_time(self):
        step = self._make_step()
        before = datetime.utcnow().isoformat()
        step.mark_running()
        assert step.status == RuntimeTaskStatus.running
        assert step.started_at is not None
        assert step.started_at >= before

    def test_mark_completed_sets_status_and_time(self):
        step = self._make_step()
        step.mark_running()
        step.mark_completed()
        assert step.status == RuntimeTaskStatus.completed
        assert step.completed_at is not None

    def test_mark_failed_records_error(self):
        step = self._make_step()
        step.mark_running()
        step.mark_failed("网络超时")
        assert step.status == RuntimeTaskStatus.failed
        assert step.error == "网络超时"
        assert step.completed_at is not None

    def test_append_log_accumulates(self):
        step = self._make_step()
        step.append_log("第一行输出")
        step.append_log("第二行输出")
        assert len(step.output_logs) == 2
        assert step.output_logs[0] == "第一行输出"
        assert step.output_logs[1] == "第二行输出"

    def test_output_logs_default_empty(self):
        step = self._make_step()
        assert step.output_logs == []

    def test_all_four_statuses_valid(self):
        for s in ("pending", "running", "completed", "failed"):
            step = self._make_step(status=s)
            assert step.status.value == s

    def test_invalid_status_raises(self):
        with pytest.raises(Exception):
            self._make_step(status="unknown")

    def test_extra_fields_ignored(self):
        step = self._make_step(some_unknown_field="value")
        assert not hasattr(step, "some_unknown_field")


# ─────────────────────────────────────────────
# REQ-SCHEMA-6: ExecutionPlan 计划级别验证
# ─────────────────────────────────────────────

class TestExecutionPlan:
    def _make_plan(self, statuses=None) -> ExecutionPlan:
        statuses = statuses or ["pending", "pending", "pending"]
        tasks = [
            ExecutionTaskStep(task_id=f"t{i}", title=f"任务{i}", status=s)
            for i, s in enumerate(statuses, 1)
        ]
        return ExecutionPlan(plan_id="plan-001", session_id="sess-001", tasks=tasks)

    def test_total_reflects_task_count(self):
        plan = self._make_plan(["pending", "running", "completed"])
        assert plan.total == 3

    def test_completed_count_only_counts_completed(self):
        plan = self._make_plan(["completed", "completed", "failed", "pending"])
        assert plan.completed_count == 2

    def test_progress_pct_all_done(self):
        plan = self._make_plan(["completed", "completed"])
        assert plan.progress_pct == 100

    def test_progress_pct_none_done(self):
        plan = self._make_plan(["pending", "pending"])
        assert plan.progress_pct == 0

    def test_progress_pct_half_done(self):
        plan = self._make_plan(["completed", "pending"])
        assert plan.progress_pct == 50

    def test_progress_pct_empty_plan(self):
        plan = ExecutionPlan(plan_id="x", session_id="y", tasks=[])
        assert plan.progress_pct == 0

    def test_get_task_by_id_found(self):
        plan = self._make_plan(["pending", "running"])
        task = plan.get_task("t1")
        assert task is not None
        assert task.title == "任务1"

    def test_get_task_by_id_not_found(self):
        plan = self._make_plan(["pending"])
        assert plan.get_task("nonexistent") is None

    def test_created_at_is_iso8601(self):
        plan = self._make_plan()
        # 应能被 datetime 解析
        dt = datetime.fromisoformat(plan.created_at)
        assert isinstance(dt, datetime)

    def test_requires_plan_id_and_session_id(self):
        with pytest.raises(Exception):
            ExecutionPlan(tasks=[])  # 缺 plan_id 和 session_id

    def test_reasoning_defaults_empty(self):
        plan = self._make_plan()
        assert plan.reasoning == ""
