from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, DateTime, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class OpenClawTask(Base):
    """
    OpenClaw 任务表 - 用于存储通过自然语言创建的任务
    支持状态追踪和幂等性
    """
    __tablename__ = "openclaw_tasks"

    task_id = Column(String(36), primary_key=True, default=generate_uuid)
    status = Column(String(20), nullable=False, default="PENDING", 
                   comment="任务状态: PENDING, DISPATCHED, FAILED")
    original_prompt = Column(Text, nullable=False, comment="原始用户提示词")
    parsed_command = Column(JSON, nullable=False, comment="解析后的命令对象")
    schedule = Column(DateTime(timezone=True), nullable=True, comment="计划执行时间")
    target_node_id = Column(String(64), nullable=True, comment="目标节点ID")
    session_id = Column(String(36), nullable=True, comment="任务会话ID (UUID v4)")
    keep_alive = Column(Boolean, default=False, comment="是否保持运行时状态")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    error_log = Column(Text, nullable=True, comment="错误日志")
    version = Column(Integer, nullable=False, default=1, comment="乐观锁版本号")

    __mapper_args__ = {
        "version_id_col": version
    }

    # 联合索引
    __table_args__ = (
        Index('idx_openclaw_tasks_status_created', 'status', 'created_at'),
        Index('idx_openclaw_tasks_created_at', 'created_at'),
        Index('idx_openclaw_tasks_session', 'session_id'),
        # 幂等性唯一约束
        Index('uq_openclaw_task', 'original_prompt', 'target_node_id', 'schedule', unique=True),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "original_prompt": self.original_prompt,
            "parsed_command": self.parsed_command,
            "schedule": self.schedule.isoformat() if self.schedule else None,
            "target_node_id": self.target_node_id,
            "session_id": self.session_id,
            "keep_alive": self.keep_alive,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "error_log": self.error_log,
        }

    @classmethod
    def get_status_choices(cls) -> list:
        """获取状态选项"""
        return ["PENDING", "DISPATCHED", "RUNNING", "COMPLETED", "FAILED"]

    @classmethod
    def validate_transition(cls, current_status: str, new_status: str):
        """
        Validate state transition.
        """
        if current_status == new_status:
            return

        allowed = {
            "PENDING": ["DISPATCHED", "FAILED"],
            "DISPATCHED": ["RUNNING", "FAILED", "COMPLETED"], # COMPLETED if instant?
            "RUNNING": ["COMPLETED", "FAILED"],
            "FAILED": ["PENDING"], # Retry
            "COMPLETED": []
        }
        
        # If current status is not in allowed map (e.g. new status added but not mapped), allow nothing or log warning
        if current_status not in allowed:
            # Fallback or strict? Strict.
            raise ValueError(f"Unknown current status: {current_status}")

        if new_status not in allowed[current_status]:
             raise ValueError(f"Invalid state transition from {current_status} to {new_status}")

    def is_pending(self) -> bool:
        """检查是否为待处理状态"""
        return self.status == "PENDING"

    def is_dispatched(self) -> bool:
        """检查是否已分发"""
        return self.status == "DISPATCHED"

    def is_failed(self) -> bool:
        """检查是否失败"""
        return self.status == "FAILED"

    def update_status(self, new_status: str, error_log: Optional[str] = None) -> None:
        """更新状态"""
        self.validate_transition(self.status, new_status)
        
        self.status = new_status
        if error_log:
            self.error_log = error_log
        self.updated_at = datetime.utcnow()