from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.eah_agent.workflow.base import EAHWorkflowState

class WorkflowNode(BaseModel):
    id: str
    name: str
    type: str = Field(..., description="Node type: agent, tool, condition, input, output")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for execution")
    inputs: List[str] = Field(default_factory=list, description="List of dependency node IDs")

class DynamicFlowState(EAHWorkflowState):
    """
    State for dynamic DAG workflows.
    """
    nodes: List[WorkflowNode] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict, description="Execution results keyed by node_id")
    execution_order: List[str] = Field(default_factory=list, description="Computed execution order")
