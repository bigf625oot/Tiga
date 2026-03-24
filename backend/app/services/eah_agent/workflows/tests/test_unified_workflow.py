"""
测试套件: app/services/eah_agent/workflows/unified_workflow.py
覆盖需求:
  - REQ-ARTIFACT-1: _snapshot_uploads_dir 正确快照目录文件及大小
  - REQ-ARTIFACT-2: _diff_uploads 仅返回新增文件，跳过已有文件
  - REQ-ARTIFACT-3: _extract_artifacts_from_text 解析 ARTIFACTS: [...] 块
  - REQ-ARTIFACT-4: _extract_artifacts_from_tool_result 从工具结果提取 /uploads/ URL
  - REQ-ARTIFACT-5: 提取结果含 size 字段（从磁盘读取）
  - REQ-ARTIFACT-6: _infer_type_from_url 正确推断文件类型
  - REQ-SSE-1: run_stream 发出 task_started 事件（含 task_id/task_name）
  - REQ-SSE-2: run_stream 发出 task_content 流式事件（含 task_id）
  - REQ-SSE-3: run_stream 发出 task_tool_call 事件（含 tool_name/status）
  - REQ-SSE-4: run_stream 发出 task_completed 事件
  - REQ-SSE-5: run_stream 发出 task_failed 事件（含 error）
  - REQ-SSE-6: run_stream 最终发出 artifacts 事件（汇总所有产出物）
  - REQ-SSE-7: plan 事件包含所有任务的初始 pending 状态列表
"""
import asyncio
import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


# ─────────────────────────────────────────────
# REQ-ARTIFACT-1/2: 目录快照与 diff
# ─────────────────────────────────────────────

class TestDirectorySnapshot:
    def test_snapshot_empty_dir(self, tmp_path):
        from app.services.eah_agent.workflows.unified_workflow import _snapshot_uploads_dir
        with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", tmp_path):
            snap = _snapshot_uploads_dir()
        assert snap == {}

    def test_snapshot_captures_files_and_sizes(self, tmp_path):
        from app.services.eah_agent.workflows.unified_workflow import _snapshot_uploads_dir
        (tmp_path / "report.md").write_text("# Hello")
        (tmp_path / "data.csv").write_text("a,b\n1,2\n")
        with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", tmp_path):
            snap = _snapshot_uploads_dir()
        assert "report.md" in snap
        assert "data.csv" in snap
        assert snap["report.md"] > 0
        assert snap["data.csv"] > 0

    def test_snapshot_ignores_subdirectories(self, tmp_path):
        from app.services.eah_agent.workflows.unified_workflow import _snapshot_uploads_dir
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file.txt").write_text("hello")
        with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", tmp_path):
            snap = _snapshot_uploads_dir()
        assert "subdir" not in snap
        assert "file.txt" in snap

    def test_snapshot_nonexistent_dir_returns_empty(self, tmp_path):
        from app.services.eah_agent.workflows.unified_workflow import _snapshot_uploads_dir
        missing = tmp_path / "nonexistent"
        with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", missing):
            snap = _snapshot_uploads_dir()
        assert snap == {}

    def test_diff_returns_only_new_files(self, tmp_path):
        from app.services.eah_agent.workflows.unified_workflow import _diff_uploads
        before = {"old.txt": 100}
        after  = {"old.txt": 100, "new.py": 250, "chart.png": 4096}
        (tmp_path / "new.py").write_bytes(b"x" * 250)
        (tmp_path / "chart.png").write_bytes(b"x" * 4096)
        with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", tmp_path):
            diff = _diff_uploads(before, after)
        names = [d["name"] for d in diff]
        assert "new.py" in names
        assert "chart.png" in names
        assert "old.txt" not in names

    def test_diff_includes_url_and_type(self, tmp_path):
        from app.services.eah_agent.workflows.unified_workflow import _diff_uploads
        before = {}
        after  = {"analysis.py": 512}
        (tmp_path / "analysis.py").write_bytes(b"x" * 512)
        with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", tmp_path):
            diff = _diff_uploads(before, after)
        assert diff[0]["url"] == "/uploads/analysis.py"
        assert diff[0]["type"] == "python"

    def test_diff_records_file_size(self, tmp_path):
        from app.services.eah_agent.workflows.unified_workflow import _diff_uploads
        before = {}
        content = b"hello world"
        (tmp_path / "result.txt").write_bytes(content)
        after = {"result.txt": len(content)}
        with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", tmp_path):
            diff = _diff_uploads(before, after)
        assert diff[0]["size"] == len(content)

    def test_diff_empty_both_returns_empty(self, tmp_path):
        from app.services.eah_agent.workflows.unified_workflow import _diff_uploads
        with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", tmp_path):
            diff = _diff_uploads({}, {})
        assert diff == []


# ─────────────────────────────────────────────
# REQ-ARTIFACT-3: ARTIFACTS 文本块解析
# ─────────────────────────────────────────────

class TestExtractArtifactsFromText:
    def _call(self, text, tmp_path=None):
        from app.services.eah_agent.workflows.unified_workflow import _extract_artifacts_from_text
        if tmp_path:
            with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", tmp_path):
                return _extract_artifacts_from_text(text)
        return _extract_artifacts_from_text(text)

    def test_parses_valid_artifacts_block(self, tmp_path):
        text = (
            '完成分析。\n'
            'ARTIFACTS: [{"name":"report.md","url":"/uploads/report.md","type":"markdown"}]'
        )
        (tmp_path / "report.md").write_text("# 报告")
        result = self._call(text, tmp_path)
        assert len(result) == 1
        assert result[0]["name"] == "report.md"
        assert result[0]["url"] == "/uploads/report.md"
        assert result[0]["type"] == "markdown"

    def test_returns_empty_when_no_artifacts_block(self):
        result = self._call("分析完成，没有产出物。")
        assert result == []

    def test_parses_multiple_artifacts(self, tmp_path):
        text = (
            'ARTIFACTS: ['
            '{"name":"a.py","url":"/uploads/a.py"},'
            '{"name":"b.csv","url":"/uploads/b.csv"}'
            ']'
        )
        (tmp_path / "a.py").write_text("code")
        (tmp_path / "b.csv").write_text("data")
        result = self._call(text, tmp_path)
        assert len(result) == 2

    def test_case_insensitive_artifacts_keyword(self, tmp_path):
        text = 'artifacts: [{"name":"f.txt","url":"/uploads/f.txt"}]'
        (tmp_path / "f.txt").write_text("hello")
        result = self._call(text, tmp_path)
        assert len(result) == 1

    def test_includes_size_from_disk(self, tmp_path):
        content = "# 报告内容"
        (tmp_path / "rep.md").write_text(content)
        text = 'ARTIFACTS: [{"name":"rep.md","url":"/uploads/rep.md","type":"markdown"}]'
        result = self._call(text, tmp_path)
        assert result[0]["size"] == (tmp_path / "rep.md").stat().st_size

    def test_returns_empty_on_malformed_json(self):
        result = self._call('ARTIFACTS: [not valid json')
        assert result == []

    def test_skips_items_without_url(self):
        result = self._call('ARTIFACTS: [{"name":"no-url.txt"}]')
        assert result == []


# ─────────────────────────────────────────────
# REQ-ARTIFACT-4/5: 工具结果中提取 URL
# ─────────────────────────────────────────────

class TestExtractArtifactsFromToolResult:
    def _call(self, text, tmp_path=None):
        from app.services.eah_agent.workflows.unified_workflow import _extract_artifacts_from_tool_result
        if tmp_path:
            with patch("app.services.eah_agent.workflows.unified_workflow._UPLOADS_DIR", tmp_path):
                return _extract_artifacts_from_tool_result(text)
        return _extract_artifacts_from_tool_result(text)

    def test_extracts_single_url(self, tmp_path):
        (tmp_path / "chart.png").write_bytes(b"\x89PNG" * 100)
        text = "Image generated: /uploads/chart.png"
        result = self._call(text, tmp_path)
        assert len(result) == 1
        assert result[0]["url"] == "/uploads/chart.png"
        assert result[0]["type"] == "image"

    def test_extracts_multiple_urls(self, tmp_path):
        (tmp_path / "a.py").write_text("code")
        (tmp_path / "b.csv").write_text("data")
        text = "Files: /uploads/a.py and /uploads/b.csv"
        result = self._call(text, tmp_path)
        urls = [r["url"] for r in result]
        assert "/uploads/a.py" in urls
        assert "/uploads/b.csv" in urls

    def test_size_zero_when_file_not_on_disk(self):
        result = self._call("File saved to /uploads/ghost.txt")
        assert result[0]["size"] == 0

    def test_returns_empty_when_no_uploads_url(self):
        result = self._call("Nothing to see here.")
        assert result == []


# ─────────────────────────────────────────────
# REQ-ARTIFACT-6: _infer_type_from_url
# ─────────────────────────────────────────────

class TestInferTypeFromUrl:
    def _call(self, url):
        from app.services.eah_agent.workflows.unified_workflow import _infer_type_from_url
        return _infer_type_from_url(url)

    @pytest.mark.parametrize("url,expected", [
        ("/uploads/script.py",    "python"),
        ("/uploads/notebook.ipynb", "notebook"),
        ("/uploads/readme.md",    "markdown"),
        ("/uploads/data.csv",     "csv"),
        ("/uploads/result.json",  "json"),
        ("/uploads/chart.png",    "image"),
        ("/uploads/photo.jpg",    "image"),
        ("/uploads/report.pdf",   "pdf"),
        ("/uploads/page.html",    "html"),
        ("/uploads/sheet.xlsx",   "excel"),
        ("/uploads/bundle.zip",   "archive"),
        ("/uploads/notes.txt",    "text"),
        ("/uploads/unknown.xyz",  "file"),
    ])
    def test_type_mapping(self, url, expected):
        assert self._call(url) == expected


# ─────────────────────────────────────────────
# REQ-SSE-1 ~ 7: run_stream 事件序列
# ─────────────────────────────────────────────

def _make_async_gen(*items):
    """辅助：把列表转为异步生成器"""
    async def _gen():
        for item in items:
            yield item
    return _gen()


def _chunk(content: str):
    c = MagicMock()
    c.content = content
    c.event = None
    return c


def _tool_chunk(tool_name: str, status: str, result: str = ""):
    c = MagicMock()
    c.content = None
    c.event = "ToolCallStarted" if status == "started" else "ToolCallCompleted"
    tool = MagicMock()
    tool.tool_name = tool_name
    tool.tool_args = {}
    if status == "completed":
        tool.result = result
    c.tool = tool
    return c


class TestRunStreamEvents:
    """
    通过 mock DB + mock Agent + mock Planner 来验证 run_stream 发出的事件序列。
    不依赖真实 LLM / 数据库 / 沙箱。
    """

    def _make_task(self, id_: int, name: str, desc: str = ""):
        t = MagicMock()
        t.id = id_
        t.name = name
        t.description = desc
        t.status = "pending"
        t.assigned_agent_role = ""
        t.result = None
        t.error = None
        return t

    def _make_plan(self, plan_id: str = "p1"):
        p = MagicMock()
        p.id = plan_id
        p.status = MagicMock()
        p.status.value = "planning"
        return p

    @pytest.mark.asyncio
    async def test_plan_event_emitted_with_task_list(self):
        """REQ-SSE-7: run_stream 发出 type='plan' 事件，包含所有 pending 任务"""
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        db = AsyncMock()
        db.execute = AsyncMock()

        task1 = self._make_task(1, "搜集数据")
        task2 = self._make_task(2, "分析数据")
        plan  = self._make_plan("plan-test")

        # Mock scalars().all() 返回两个任务
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [task1, task2]
        result_mock.scalars.return_value.first.side_effect = [plan, task1, task2, None]
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()
        db.flush = AsyncMock()

        workflow = UnifiedAgentWorkflow(
            session_id="sess-test", db=db, user_goal="分析销售数据"
        )

        events = []
        with (
            patch("app.services.eah_agent.workflows.unified_workflow.PlannerAgent.create_plan",
                  new_callable=AsyncMock, return_value="plan-test"),
            patch.object(workflow, "kb_manager"),
            patch.object(workflow, "state_manager", new=MagicMock(update_mode=AsyncMock(), save_state=AsyncMock())),
            patch.object(workflow, "compressor", new=MagicMock(compress_context=AsyncMock(return_value=[]))),
            patch.object(workflow, "_create_executor_agent", new_callable=AsyncMock),
            patch.object(workflow, "_get_plan", new_callable=AsyncMock, return_value=plan),
            patch.object(workflow, "_get_next_task", new_callable=AsyncMock,
                         side_effect=[task1, task2, None]),
        ):
            # Make executor agent stream a single content chunk then stop
            executor_mock = MagicMock()
            executor_mock.arun.return_value = _make_async_gen(_chunk("结果"))
            workflow._create_executor_agent.return_value = executor_mock
            workflow.kb_manager.get_knowledge_base.return_value = None

            async for event in workflow.run_stream():
                events.append(event)

        event_types = [e.get("type") for e in events]
        assert "plan" in event_types

        plan_event = next(e for e in events if e.get("type") == "plan")
        assert "plan" in plan_event
        assert "tasks" in plan_event["plan"]

    @pytest.mark.asyncio
    async def test_task_started_event_per_task(self):
        """REQ-SSE-1: 每个任务执行前应发出 task_started 事件，含 task_id 和 task_name"""
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        db = AsyncMock()
        task = self._make_task(42, "数据清洗", "清洗原始数据")
        plan = self._make_plan("p42")

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [task]
        result_mock.scalars.return_value.first.side_effect = [plan, task, None]
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()

        workflow = UnifiedAgentWorkflow(session_id="s", db=db, user_goal="清洗数据")
        events = []
        with (
            patch("app.services.eah_agent.workflows.unified_workflow.PlannerAgent.create_plan",
                  new_callable=AsyncMock, return_value="p42"),
            patch.object(workflow, "kb_manager"),
            patch.object(workflow, "state_manager", new=MagicMock(update_mode=AsyncMock(), save_state=AsyncMock())),
            patch.object(workflow, "compressor", new=MagicMock(compress_context=AsyncMock(return_value=[]))),
            patch.object(workflow, "_get_plan", new_callable=AsyncMock, return_value=plan),
            patch.object(workflow, "_get_next_task", new_callable=AsyncMock,
                         side_effect=[task, None]),
            patch.object(workflow, "_create_executor_agent", new_callable=AsyncMock),
            patch("app.services.eah_agent.workflows.unified_workflow._snapshot_uploads_dir",
                  return_value={}),
            patch("app.services.eah_agent.workflows.unified_workflow._diff_uploads",
                  return_value=[]),
        ):
            executor_mock = MagicMock()
            executor_mock.arun.return_value = _make_async_gen(_chunk("done"))
            workflow._create_executor_agent.return_value = executor_mock
            workflow.kb_manager.get_knowledge_base.return_value = None

            async for event in workflow.run_stream():
                events.append(event)

        started = [e for e in events if e.get("type") == "task_started"]
        assert len(started) == 1
        assert started[0]["task_id"] == "42"
        assert started[0]["task_name"] == "数据清洗"

    @pytest.mark.asyncio
    async def test_task_content_event_streamed(self):
        """REQ-SSE-2: 流式内容应通过 task_content 事件推送，含 task_id"""
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        db = AsyncMock()
        task = self._make_task(7, "生成报告")
        plan = self._make_plan("p7")

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [task]
        result_mock.scalars.return_value.first.side_effect = [plan, task, None]
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()

        workflow = UnifiedAgentWorkflow(session_id="s", db=db, user_goal="报告")
        events = []
        with (
            patch("app.services.eah_agent.workflows.unified_workflow.PlannerAgent.create_plan",
                  new_callable=AsyncMock, return_value="p7"),
            patch.object(workflow, "kb_manager"),
            patch.object(workflow, "state_manager", new=MagicMock(update_mode=AsyncMock(), save_state=AsyncMock())),
            patch.object(workflow, "compressor", new=MagicMock(compress_context=AsyncMock(return_value=[]))),
            patch.object(workflow, "_get_plan", new_callable=AsyncMock, return_value=plan),
            patch.object(workflow, "_get_next_task", new_callable=AsyncMock,
                         side_effect=[task, None]),
            patch.object(workflow, "_create_executor_agent", new_callable=AsyncMock),
            patch("app.services.eah_agent.workflows.unified_workflow._snapshot_uploads_dir",
                  return_value={}),
            patch("app.services.eah_agent.workflows.unified_workflow._diff_uploads",
                  return_value=[]),
        ):
            executor_mock = MagicMock()
            executor_mock.arun.return_value = _make_async_gen(
                _chunk("第一段"), _chunk("第二段")
            )
            workflow._create_executor_agent.return_value = executor_mock
            workflow.kb_manager.get_knowledge_base.return_value = None

            async for event in workflow.run_stream():
                events.append(event)

        content_events = [e for e in events if e.get("type") == "task_content"]
        contents = [e["content"] for e in content_events]
        assert "第一段" in contents
        assert "第二段" in contents
        assert all(e["task_id"] == "7" for e in content_events)

    @pytest.mark.asyncio
    async def test_task_tool_call_event(self):
        """REQ-SSE-3: 工具调用发出 task_tool_call 事件，含 tool_name 和 status"""
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        db = AsyncMock()
        task = self._make_task(5, "执行代码")
        plan = self._make_plan("p5")

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [task]
        result_mock.scalars.return_value.first.side_effect = [plan, task, None]
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()

        workflow = UnifiedAgentWorkflow(session_id="s", db=db, user_goal="执行")
        events = []
        with (
            patch("app.services.eah_agent.workflows.unified_workflow.PlannerAgent.create_plan",
                  new_callable=AsyncMock, return_value="p5"),
            patch.object(workflow, "kb_manager"),
            patch.object(workflow, "state_manager", new=MagicMock(update_mode=AsyncMock(), save_state=AsyncMock())),
            patch.object(workflow, "compressor", new=MagicMock(compress_context=AsyncMock(return_value=[]))),
            patch.object(workflow, "_get_plan", new_callable=AsyncMock, return_value=plan),
            patch.object(workflow, "_get_next_task", new_callable=AsyncMock,
                         side_effect=[task, None]),
            patch.object(workflow, "_create_executor_agent", new_callable=AsyncMock),
            patch("app.services.eah_agent.workflows.unified_workflow._snapshot_uploads_dir",
                  return_value={}),
            patch("app.services.eah_agent.workflows.unified_workflow._diff_uploads",
                  return_value=[]),
        ):
            executor_mock = MagicMock()
            executor_mock.arun.return_value = _make_async_gen(
                _tool_chunk("run_code", "started"),
                _tool_chunk("run_code", "completed", result="output"),
                _chunk("结束"),
            )
            workflow._create_executor_agent.return_value = executor_mock
            workflow.kb_manager.get_knowledge_base.return_value = None

            async for event in workflow.run_stream():
                events.append(event)

        tool_events = [e for e in events if e.get("type") == "task_tool_call"]
        assert len(tool_events) == 2
        assert tool_events[0]["tool"]["tool_name"] == "run_code"
        assert tool_events[0]["tool"]["status"] == "started"
        assert tool_events[1]["tool"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_task_completed_event(self):
        """REQ-SSE-4: 任务正常结束后发出 task_completed 事件"""
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        db = AsyncMock()
        task = self._make_task(3, "完成任务")
        plan = self._make_plan("p3")

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [task]
        result_mock.scalars.return_value.first.side_effect = [plan, task, None]
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()

        workflow = UnifiedAgentWorkflow(session_id="s", db=db, user_goal="任务")
        events = []
        with (
            patch("app.services.eah_agent.workflows.unified_workflow.PlannerAgent.create_plan",
                  new_callable=AsyncMock, return_value="p3"),
            patch.object(workflow, "kb_manager"),
            patch.object(workflow, "state_manager", new=MagicMock(update_mode=AsyncMock(), save_state=AsyncMock())),
            patch.object(workflow, "compressor", new=MagicMock(compress_context=AsyncMock(return_value=[]))),
            patch.object(workflow, "_get_plan", new_callable=AsyncMock, return_value=plan),
            patch.object(workflow, "_get_next_task", new_callable=AsyncMock,
                         side_effect=[task, None]),
            patch.object(workflow, "_create_executor_agent", new_callable=AsyncMock),
            patch("app.services.eah_agent.workflows.unified_workflow._snapshot_uploads_dir",
                  return_value={}),
            patch("app.services.eah_agent.workflows.unified_workflow._diff_uploads",
                  return_value=[]),
        ):
            executor_mock = MagicMock()
            executor_mock.arun.return_value = _make_async_gen(_chunk("完成"))
            workflow._create_executor_agent.return_value = executor_mock
            workflow.kb_manager.get_knowledge_base.return_value = None

            async for event in workflow.run_stream():
                events.append(event)

        completed = [e for e in events if e.get("type") == "task_completed"]
        assert len(completed) == 1
        assert completed[0]["task_id"] == "3"

    @pytest.mark.asyncio
    async def test_task_failed_event_on_executor_exception(self):
        """REQ-SSE-5: executor 抛出异常时发出 task_failed 事件，含 error 字段"""
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        db = AsyncMock()
        task = self._make_task(9, "失败任务")
        plan = self._make_plan("p9")

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [task]
        result_mock.scalars.return_value.first.side_effect = [plan, task, None]
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()

        workflow = UnifiedAgentWorkflow(session_id="s", db=db, user_goal="任务")
        events = []
        with (
            patch("app.services.eah_agent.workflows.unified_workflow.PlannerAgent.create_plan",
                  new_callable=AsyncMock, return_value="p9"),
            patch.object(workflow, "kb_manager"),
            patch.object(workflow, "state_manager", new=MagicMock(update_mode=AsyncMock(), save_state=AsyncMock())),
            patch.object(workflow, "compressor", new=MagicMock(compress_context=AsyncMock(return_value=[]))),
            patch.object(workflow, "_get_plan", new_callable=AsyncMock, return_value=plan),
            patch.object(workflow, "_get_next_task", new_callable=AsyncMock,
                         side_effect=[task, None]),
            patch.object(workflow, "_create_executor_agent",
                         new_callable=AsyncMock,
                         side_effect=RuntimeError("网络中断")),
            patch("app.services.eah_agent.workflows.unified_workflow._snapshot_uploads_dir",
                  return_value={}),
        ):
            workflow.kb_manager.get_knowledge_base.return_value = None

            async for event in workflow.run_stream():
                events.append(event)

        failed = [e for e in events if e.get("type") == "task_failed"]
        assert len(failed) == 1
        assert failed[0]["task_id"] == "9"
        assert "网络中断" in failed[0]["error"]

    @pytest.mark.asyncio
    async def test_artifacts_event_emitted_at_end(self):
        """REQ-SSE-6: 所有任务完成后，若有新文件，发出 artifacts 事件"""
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        db = AsyncMock()
        task = self._make_task(1, "生成文件")
        plan = self._make_plan("p1")

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [task]
        result_mock.scalars.return_value.first.side_effect = [plan, task, None]
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()

        workflow = UnifiedAgentWorkflow(session_id="s", db=db, user_goal="生成")
        events = []
        new_file = {"name": "result.py", "url": "/uploads/result.py", "type": "python", "size": 128}
        with (
            patch("app.services.eah_agent.workflows.unified_workflow.PlannerAgent.create_plan",
                  new_callable=AsyncMock, return_value="p1"),
            patch.object(workflow, "kb_manager"),
            patch.object(workflow, "state_manager", new=MagicMock(update_mode=AsyncMock(), save_state=AsyncMock())),
            patch.object(workflow, "compressor", new=MagicMock(compress_context=AsyncMock(return_value=[]))),
            patch.object(workflow, "_get_plan", new_callable=AsyncMock, return_value=plan),
            patch.object(workflow, "_get_next_task", new_callable=AsyncMock,
                         side_effect=[task, None]),
            patch.object(workflow, "_create_executor_agent", new_callable=AsyncMock),
            patch("app.services.eah_agent.workflows.unified_workflow._snapshot_uploads_dir",
                  return_value={}),
            patch("app.services.eah_agent.workflows.unified_workflow._diff_uploads",
                  return_value=[new_file]),
            patch("app.services.eah_agent.workflows.unified_workflow._extract_artifacts_from_text",
                  return_value=[]),
        ):
            executor_mock = MagicMock()
            executor_mock.arun.return_value = _make_async_gen(_chunk("output"))
            workflow._create_executor_agent.return_value = executor_mock
            workflow.kb_manager.get_knowledge_base.return_value = None

            async for event in workflow.run_stream():
                events.append(event)

        artifact_events = [e for e in events if e.get("type") == "artifacts"]
        assert len(artifact_events) == 1
        files = artifact_events[0]["files"]
        assert any(f["url"] == "/uploads/result.py" for f in files)

    @pytest.mark.asyncio
    async def test_no_artifacts_event_when_no_new_files(self):
        """REQ-SSE-6: 没有新文件时不应发出 artifacts 事件"""
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        db = AsyncMock()
        task = self._make_task(1, "无文件任务")
        plan = self._make_plan("p0")

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [task]
        result_mock.scalars.return_value.first.side_effect = [plan, task, None]
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()

        workflow = UnifiedAgentWorkflow(session_id="s", db=db, user_goal="无文件")
        events = []
        with (
            patch("app.services.eah_agent.workflows.unified_workflow.PlannerAgent.create_plan",
                  new_callable=AsyncMock, return_value="p0"),
            patch.object(workflow, "kb_manager"),
            patch.object(workflow, "state_manager", new=MagicMock(update_mode=AsyncMock(), save_state=AsyncMock())),
            patch.object(workflow, "compressor", new=MagicMock(compress_context=AsyncMock(return_value=[]))),
            patch.object(workflow, "_get_plan", new_callable=AsyncMock, return_value=plan),
            patch.object(workflow, "_get_next_task", new_callable=AsyncMock,
                         side_effect=[task, None]),
            patch.object(workflow, "_create_executor_agent", new_callable=AsyncMock),
            patch("app.services.eah_agent.workflows.unified_workflow._snapshot_uploads_dir",
                  return_value={}),
            patch("app.services.eah_agent.workflows.unified_workflow._diff_uploads",
                  return_value=[]),
            patch("app.services.eah_agent.workflows.unified_workflow._extract_artifacts_from_text",
                  return_value=[]),
        ):
            executor_mock = MagicMock()
            executor_mock.arun.return_value = _make_async_gen(_chunk("done"))
            workflow._create_executor_agent.return_value = executor_mock
            workflow.kb_manager.get_knowledge_base.return_value = None

            async for event in workflow.run_stream():
                events.append(event)

        assert not any(e.get("type") == "artifacts" for e in events)
