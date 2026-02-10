from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from agno.agent import Agent

class AgentContext(BaseModel):
    """
    Unified context data model for all steps in the workflow.
    """
    session_id: str = Field(..., description="The unique session identifier")
    user_message: str = Field(..., description="The current user input message")
    history: List[Dict[str, Any]] = Field(default_factory=list, description="Chat history")
    
    # RAG related
    doc_ids: List[str] = Field(default_factory=list, description="Document IDs for retrieval")
    retrieved_references: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved context/documents")
    
    # Execution related
    agent_id: Optional[str] = None
    agent_config: Optional[Dict[str, Any]] = None
    model_config_data: Optional[Dict[str, Any]] = Field(None, alias="model_config")
    
    # Workflow control
    current_step: str = "init"
    next_step: Optional[str] = None
    should_stop: bool = False
    error: Optional[str] = None
    
    # Output
    output_stream: Any = None # Iterator or similar, hard to serialize
    final_response: Optional[str] = None
    reasoning_content: Optional[str] = None
    
    # Metadata
    meta: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

class WorkflowSessionState(BaseModel):
    """
    Session state for the workflow, persisting across steps.
    """
    session_id: str
    context: AgentContext
    step_history: List[str] = Field(default_factory=list)
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    circuit_breaker_status: Dict[str, Any] = Field(default_factory=dict)
