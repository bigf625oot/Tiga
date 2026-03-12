"""
研究报告工作流状态定义
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.eah_agent.workflow.base import EAHWorkflowState

class ResearchStep(BaseModel):
    name: str
    status: str = "pending" # pending, running, completed, failed
    output: Optional[str] = None

class ResearchFlowState(EAHWorkflowState):
    query: str = Field(..., description="研究课题")
    steps: List[ResearchStep] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict)
    report_content: Optional[str] = None
