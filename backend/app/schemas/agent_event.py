"""
Agent Event Schemas
数据契约：后端 → 前端的 SSE 推送协议。

事件类型（与前端 AgentEventType 严格对应）：
  thought      — 左侧：流式思维链（纯文本，流式追加）
  plan_created — 右侧：初始化任务列表（JSON ExecutionPlan）
  task_start   — 右侧：某步骤进入 running 状态
  tool_call    — 左侧：弹出工具调用条
  tool_output  — 右侧：实时日志流 / 控制台输出
  artifact     — 左右配合：产出物卡片
  summary      — 左侧：最终总结陈词
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


# ─── 枚举 ────────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    pending   = "pending"
    running   = "running"
    completed = "completed"
    failed    = "failed"


class ArtifactType(str, Enum):
    image    = "image"
    csv      = "csv"
    pdf      = "pdf"
    code     = "code"
    markdown = "markdown"
    notebook = "notebook"
    excel    = "excel"
    archive  = "archive"
    text     = "text"
    file     = "file"  # 兜底


class EventType(str, Enum):
    thought      = "thought"
    plan_created = "plan_created"
    task_start   = "task_start"
    tool_call    = "tool_call"
    tool_output  = "tool_output"
    artifact     = "artifact"
    summary      = "summary"


# ─── 子结构 ──────────────────────────────────────────────────────────────────

class TaskStep(BaseModel):
    """右侧任务清单的单步结构"""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="任务 ID")
    title: str = Field(..., description="任务标题")
    status: TaskStatus = Field(default=TaskStatus.pending)
    description: str = Field(default="")
    assigned_role: str = Field(default="")
    dependencies: List[str] = Field(default_factory=list, description="依赖的前置任务 ID 列表")


class ExecutionPlan(BaseModel):
    """Agent 生成的初始执行计划"""
    model_config = ConfigDict(extra="ignore")

    plan_id: str = Field(..., description="计划 ID")
    reasoning: str = Field(default="", description="规划思路摘要")
    tasks: List[TaskStep] = Field(default_factory=list)


class ToolCallInfo(BaseModel):
    """工具调用信息（tool_call 事件）"""
    tool: str = Field(..., description="工具名称")
    args: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None


class ToolOutputInfo(BaseModel):
    """工具执行结果（tool_output 事件）"""
    tool: str = Field(..., description="工具名称")
    output: Any = Field(default=None)
    logs: List[str] = Field(default_factory=list, description="执行日志行")
    is_error: bool = False
    task_id: Optional[str] = None


class TaskStartInfo(BaseModel):
    """任务开始（task_start 事件）"""
    task_id: str
    title: str = ""
    status: TaskStatus = TaskStatus.running


class ArtifactCard(BaseModel):
    """产出物卡片（artifact 事件）"""
    model_config = ConfigDict(extra="ignore")

    file_name: str = Field(..., description="文件名")
    file_size: int = Field(default=0, description="文件大小（字节）")
    url: str = Field(..., description="公共静态链接 /uploads/...")
    type: ArtifactType = Field(default=ArtifactType.file)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ArtifactCard":
        raw_type = d.get("type", "file")
        _type_map = {
            "python": ArtifactType.code,
            "notebook": ArtifactType.notebook,
        }
        artifact_type = _type_map.get(raw_type) or (
            ArtifactType(raw_type) if raw_type in ArtifactType._value2member_map_ else ArtifactType.file
        )
        return cls(
            file_name=d.get("name", ""),
            file_size=d.get("size", 0),
            url=d.get("url", ""),
            type=artifact_type,
        )


# ─── 顶层 AgentEvent ─────────────────────────────────────────────────────────

class AgentEvent(BaseModel):
    """统一 SSE 推送结构，每条事件序列化为 `data: <json>\\n\\n`"""
    model_config = ConfigDict(extra="ignore")

    agent_run_id: str = Field(..., description="任务唯一标识")
    type: EventType
    content: Any = Field(..., description="事件内容，随 type 变化")
    task_id: Optional[str] = Field(default=None, description="关联的右侧 TaskStep ID")
    elapsed_ms: Optional[int] = Field(default=None)
    token_usage: Optional[int] = Field(default=None)

    def sse_encode(self) -> str:
        return f"event: {self.type.value}\ndata: {self.model_dump_json()}\n\n"

    # ── 便捷构造 ────────────────────────��────────────────────────────────────

    @classmethod
    def thought(cls, run_id: str, text: str, **kw) -> "AgentEvent":
        return cls(agent_run_id=run_id, type=EventType.thought, content=text, **kw)

    @classmethod
    def plan_created(cls, run_id: str, plan: ExecutionPlan, **kw) -> "AgentEvent":
        return cls(agent_run_id=run_id, type=EventType.plan_created, content=plan.model_dump(), **kw)

    @classmethod
    def task_start(cls, run_id: str, info: TaskStartInfo, **kw) -> "AgentEvent":
        return cls(agent_run_id=run_id, type=EventType.task_start, content=info.model_dump(), task_id=info.task_id, **kw)

    @classmethod
    def tool_call(cls, run_id: str, info: ToolCallInfo, **kw) -> "AgentEvent":
        return cls(agent_run_id=run_id, type=EventType.tool_call, content=info.model_dump(), task_id=info.task_id, **kw)

    @classmethod
    def tool_output(cls, run_id: str, info: ToolOutputInfo, **kw) -> "AgentEvent":
        return cls(agent_run_id=run_id, type=EventType.tool_output, content=info.model_dump(), task_id=info.task_id, **kw)

    @classmethod
    def artifact(cls, run_id: str, card: ArtifactCard, task_id: Optional[str] = None, **kw) -> "AgentEvent":
        return cls(agent_run_id=run_id, type=EventType.artifact, content=card.model_dump(), task_id=task_id, **kw)

    @classmethod
    def summary(cls, run_id: str, text: str, **kw) -> "AgentEvent":
        return cls(agent_run_id=run_id, type=EventType.summary, content=text, **kw)
