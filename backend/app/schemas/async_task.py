from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AsyncTaskCreate(BaseModel):
    name: str = Field(..., description="任务名称")
    task_type: str = Field(default="GENERAL", description="任务类型")
    priority: int = Field(default=1, ge=0, le=9, description="优先级 0-9")
    context: Optional[Dict[str, Any]] = Field(default=None, description="额外上下文")


class AsyncTaskProgressUpdate(BaseModel):
    percent: int = Field(..., ge=0, le=100, description="进度百分比")
    status: str = Field(..., description="状态: RUNNING/SUCCESS/FAILED")
    msg: str = Field(default="", description="状态消息")
    step: str = Field(default="", description="当前步骤")
    extend: Optional[Dict[str, Any]] = Field(default=None, description="扩展数据")


class AsyncTaskResponse(BaseModel):
    id: str
    name: str
    task_type: str
    status: str
    progress: int = 0
    msg: str = ""
    step: str = ""
    priority: int
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AsyncTaskListResponse(BaseModel):
    items: List[AsyncTaskResponse]
    total: int
    page: int = 1
    page_size: int = 20


class AsyncTaskCreateResponse(BaseModel):
    task_id: str
    estimate_time: Optional[int] = Field(default=None, description="预估耗时(秒)")
    message: str = "任务已提交"


class WebSocketMessage(BaseModel):
    type: str = Field(..., description="消息类型: progress/result/error")
    task_id: str
    data: Dict[str, Any]