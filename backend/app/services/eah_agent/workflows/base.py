"""
存放工作流基类、通用的状态(State)定义
"""

from typing import Any, Dict, Optional, AsyncGenerator
from agno.workflow import Workflow
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class EAHWorkflowState(BaseModel):
    """EAH 工作流的基础状态定义"""
    session_id: str = Field(..., description="会话 ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文数据")
    current_step: str = Field("init", description="当前执行步骤")
    steps_completed: list[str] = Field(default_factory=list, description="已完成的步骤列表")
    error: Optional[str] = Field(None, description="错误信息")

class EAHWorkflow(Workflow):
    """
    Expert AI Hub (EAH) 工作流基类，继承自 Agno Workflow。
    """
    def __init__(self, session_id: str, **kwargs):
        self.session_id = session_id
        # 初始化状态，如果子类没有定义更具体的状态，则使用基础状态
        if not hasattr(self, "state") or self.state is None:
            # Note: Agno Workflow might manage 'state' internally via Pydantic model
            # Here we ensure it's initialized with our base fields
            self.state = EAHWorkflowState(session_id=session_id)
        
        # 设置工作流名称
        if "name" not in kwargs:
            kwargs["name"] = self.__class__.__name__
            
        super().__init__(**kwargs)

    async def run(self, *args, **kwargs) -> Any:
        """同步运行入口，需在子类中实现"""
        raise NotImplementedError("Workflows must implement run()")

    async def run_stream(self, *args, **kwargs) -> AsyncGenerator[str, None]:
        """流式运行入口，需在子类中实现"""
        raise NotImplementedError("Workflows must implement run_stream()")
