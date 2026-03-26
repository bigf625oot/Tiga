import json
import re
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional, Dict, Generator, Type, TypeVar
from pydantic import BaseModel, Field, ValidationError, ConfigDict

# --- 1. 深度增强型异常体系 ---

class PlanError(Exception):
    """基础异常：携带上下文诊断信息"""
    def __init__(self, message: str, raw_content: Optional[str] = None, diagnostics: Optional[Dict] = None):
        super().__init__(message)
        self.raw_content = raw_content
        self.diagnostics = diagnostics or {}

class PlanParseError(PlanError):
    """解析阶段失败：文本不含合法JSON结构"""
    pass

class PlanValidationError(PlanError):
    """验证阶段失败：结构合法但业务规则校验未通过"""
    def __init__(self, message: str, errors: Optional[List[Dict]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.validation_details = errors or []

# --- 2. 强类型业务模型 ---

class TaskStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra='ignore')
    
    id: int = Field(..., description="步骤索引")
    task: str = Field(..., min_length=1, description="任务描述内容")
    tool_name: str = Field(..., description="目标工具名")
    dependencies: List[int] = Field(default_factory=list, description="依赖的前置ID列表")

class TaskPlan(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='ignore')
    
    steps: List[TaskStep] = Field(..., description="执行步骤集合")
    estimated_reasoning: str = Field(default="", description="大模型思考链路")
    version: str = Field(default="v1")

T = TypeVar("T", bound=BaseModel)

# --- 3. 工业级解析引擎 ---

class JsonFixer:
    """具备自愈能力的 JSON 净化器"""
    _FENCES = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
    _PY_CONST = re.compile(r"\b(True|False|None)\b")
    _TRAILING_COMMA = re.compile(r",\s*([\]}])")
    _SINGLE_QUOTE_KEY = re.compile(r"'(\w+)'\s*:") # 修复单引号key
    _CONTROL_CHARS = re.compile(r"[\x00-\x1F\x7F]") # 移除不可见控制字符

    @classmethod
    def clean(cls, text: str) -> str:
        t = text.strip()
        # 移除不可见字符（LLM有时会输出乱码）
        t = cls._CONTROL_CHARS.sub("", t)
        # 修正 Python 特有布尔值/空值
        t = cls._PY_CONST.sub(lambda m: {"True":"true","False":"false","None":"null"}[m.group(1)], t)
        # 修正单引号 key (例如 'steps': -> "steps":)
        t = cls._SINGLE_QUOTE_KEY.sub(r'"\1":', t)
        # 移除 JSON 数组或对象末尾多余的逗号
        t = cls._TRAILING_COMMA.sub(r"\1", t)
        return t

class TaskPlanParser:
    """
    终极协议解析器：
    采用 预清洗 -> 启发式提取 -> 深度验证 -> 错误回溯 的闭环逻辑
    """
    
    def __init__(self, model_class: Type[T] = TaskPlan):
        self.model_class = model_class
        self.logger = logging.getLogger("TaskPlanParser")

    def _yield_candidates(self, raw_text: str) -> Generator[str, None, None]:
        """启发式候选块生成器"""
        # 1. 优先级最高：Markdown 代码块
        found_fence = False
        for match in JsonFixer._FENCES.finditer(raw_text):
            found_fence = True
            yield match.group(1)
        
        # 2. 优先级中等：首尾大括号贪婪匹配
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            # 如果之前没找到过 fence，或者这个括号块比 fence 长，则尝试
            yield raw_text[start : end + 1]
        
        # 3. 优先级低：全文直接尝试
        if not found_fence:
            yield raw_text

    def _validate_dict(self, payload: Dict, raw_input: str) -> T:
        """
        深度验证：将 Pydantic 晦涩的错误转化为开发者和 LLM 都能秒懂的描述
        """
        try:
            return self.model_class.model_validate(payload)
        except ValidationError as e:
            readable_errors = []
            for err in e.errors():
                # 构造路径：例如 "steps.0.tool_name"
                loc = ".".join(str(p) for p in err['loc'])
                msg = err['msg']
                input_val = err.get('input', 'N/A')
                readable_errors.append({
                    "path": loc,
                    "issue": msg,
                    "received": input_val
                })
            
            # 记录详细日志供审计
            self.logger.warning(f"Validation failed for schema {self.model_class.__name__}: {readable_errors}")
            
            raise PlanValidationError(
                message=f"Schema validation failed: Found {len(readable_errors)} issues.",
                errors=readable_errors,
                raw_content=raw_input,
                diagnostics={"type": "pydantic_validation_error"}
            )

    def parse(self, data: Any) -> T:
        """解析主逻辑"""
        if isinstance(data, self.model_class):
            return data
        
        if isinstance(data, dict):
            return self._validate_dict(data, str(data))

        if not isinstance(data, str):
            raise PlanError(f"Critical: Expected string or dict, got {type(data)}")

        last_err = None
        # 尝试所有候选文本块
        for candidate in self._yield_candidates(data):
            cleaned = JsonFixer.clean(candidate)
            try:
                # 1. 尝试 JSON 反序列化
                obj = json.loads(cleaned)
                if not isinstance(obj, dict):
                    continue
                # 2. 尝试 Pydantic 业务验证
                return self._validate_dict(obj, data)
            except (json.JSONDecodeError, PlanValidationError) as e:
                last_err = e
                continue

        # 最终兜底：如果循环结束还没返回，抛出汇总异常
        if isinstance(last_err, PlanValidationError):
            raise last_err
        
        raise PlanParseError(
            message="Failed to extract a valid TaskPlan JSON structure from the output.",
            raw_content=data,
            diagnostics={"error_type": "extraction_failure"}
        )


_DEFAULT_TASK_PLAN_PARSER = TaskPlanParser(TaskPlan)


def parse_task_plan(value: Any) -> TaskPlan:
    try:
        return _DEFAULT_TASK_PLAN_PARSER.parse(value)
    except PlanValidationError:
        raise
    except PlanError as e:
        raise PlanValidationError(
            message=str(e),
            raw_content=getattr(e, "raw_content", None),
            diagnostics=getattr(e, "diagnostics", None),
        )

# --- 4. 运行时执行计划 Schema (Runtime Execution Schema) ---

class RuntimeTaskStatus(str, Enum):
    """任务运行时状态枚举 — 严格四态"""
    pending   = "pending"
    running   = "running"
    completed = "completed"
    failed    = "failed"


class ExecutionTaskStep(BaseModel):
    """
    运行时单任务的完整描述，包含状态与输出日志。
    由后端在执行过程中持续更新，并通过 SSE 推送前端。
    """
    model_config = ConfigDict(extra='ignore')

    task_id: str = Field(..., description="全局唯一任务 ID，与 DB 主键对齐")
    title: str = Field(..., description="任务标题（100 字以内）")
    description: str = Field(default="", description="详细执行描述")
    status: RuntimeTaskStatus = Field(default=RuntimeTaskStatus.pending, description="四态状态机")
    output_logs: List[str] = Field(default_factory=list, description="按时间序追加的输出行")
    dependencies: List[str] = Field(default_factory=list, description="依赖的前置 task_id 列表")
    executor_role: str = Field(default="", description="执行角色，如 'coder', 'researcher'")
    expected_output: str = Field(default="Execute successfully", description="预期输出")
    reflection: Optional[str] = Field(default=None, description="反思提示")
    started_at: Optional[str] = Field(default=None, description="ISO8601 开始时间")
    completed_at: Optional[str] = Field(default=None, description="ISO8601 完成时间")
    error: Optional[str] = Field(default=None, description="失败时的错误摘要")

    def mark_running(self) -> None:
        self.status = RuntimeTaskStatus.running
        self.started_at = datetime.now(timezone.utc).isoformat()

    def mark_completed(self) -> None:
        self.status = RuntimeTaskStatus.completed
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self, error: str) -> None:
        self.status = RuntimeTaskStatus.failed
        self.error = error
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def append_log(self, line: str) -> None:
        self.output_logs.append(line)


class ExecutionPlan(BaseModel):
    """
    完整执行计划 — Schema 规范：由 Planner 生成后在整个执行生命周期中保持同步。
    前端通过 SSE type='plan' 事件接收此结构的序列化形式。
    """
    model_config = ConfigDict(extra='ignore')

    plan_id: str = Field(..., description="DB 计划主键字符串")
    session_id: str = Field(..., description="关联会话 ID")
    user_goal: str = Field(default="", description="原始用户目标")
    reasoning: str = Field(default="", description="LLM 规划思路")
    tasks: List[ExecutionTaskStep] = Field(..., description="有序任务列表")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="计划创建时间"
    )

    @property
    def total(self) -> int:
        return len(self.tasks)

    @property
    def completed_count(self) -> int:
        return sum(1 for t in self.tasks if t.status == RuntimeTaskStatus.completed)

    @property
    def progress_pct(self) -> int:
        if self.total == 0:
            return 0
        return round(self.completed_count / self.total * 100)

    def get_task(self, task_id: str) -> Optional[ExecutionTaskStep]:
        return next((t for t in self.tasks if t.task_id == task_id), None)
