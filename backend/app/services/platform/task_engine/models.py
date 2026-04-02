from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class TaskEngineType(str, Enum):
    """底层任务引擎的类型枚举"""
    ASYNC_TASK = "async_task"         # 通用异步任务（默认进程内/协程池）
    EXECUTION = "execution"           # 复杂执行编排（带子任务）
    PATHWAY = "pathway"               # 数据流水线作业
    CELERY = "celery"                 # 横向扩展分布式队列


class TaskEvent(BaseModel):
    """引擎回传给统一任务中心的标准化事件"""
    task_id: str
    status: str
    progress: int = 0
    message: str = ""
    step: str = ""
    extend_data: Optional[Dict[str, Any]] = None


class TaskRunContext(BaseModel):
    """启动任务时传递的上下文（包含统一的 task_id 与特定引擎需要的配置）"""
    task_id: str
    engine_type: TaskEngineType
    user_id: Optional[str] = None
    priority: int = 1
    config: Dict[str, Any] = Field(default_factory=dict)
