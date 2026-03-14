"""
研究报告工作流状态定义
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.eah_agent.workflows.base import EAHWorkflowState

class ReportSection(BaseModel):
    title: str
    content: str
    order: int

class ReportFlowState(EAHWorkflowState):
    data_source: str = Field(..., description="数据来源")
    sections: List[ReportSection] = Field(default_factory=list)
    final_report: Optional[str] = None
