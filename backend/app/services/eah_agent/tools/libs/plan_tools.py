from typing import List, Dict, Optional, Any
from agno.tools import Toolkit
from pydantic import BaseModel, Field, validator

class PlanStep(BaseModel):
    title: str = Field(..., description="The title of the step")
    description: Optional[str] = Field(None, description="A short description")
    status: str = Field(..., description="Status: pending, running, completed, failed")
    dependencies: List[str] = Field(default=[], description="List of step titles this step depends on")
    task_type: Optional[str] = Field(None, description="Type of task: search, code, file, etc.")

    @validator("status")
    def validate_status(cls, v):
        allowed = {"pending", "running", "completed", "failed"}
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v.lower()

class PlanTools(Toolkit):
    _name = "plan_tools"
    _label = "任务规划 (Plan)"
    _description = "管理和更新任务执行计划"
    """
    使用 PlanTools 管理任务计划。
    Agent 必须在开始任务前调用 `update_plan` 创建初始计划，并在任务执行过程中根据实际情况更新计划状态。
    支持定义任务依赖关系，确保执行顺序。
    """

    def __init__(self):
        super().__init__(name="plan_tools")
        self.register(self.update_plan)

    def update_plan(self, steps: List[Dict[str, Any]]) -> str:
        """
        Create or update the execution plan.
        
        Args:
            steps: A list of steps. Each step must have:
                   - title: The name of the step.
                   - description: A short description (optional).
                   - status: One of "pending", "running", "completed", "failed".
                   - dependencies: List of step titles this step depends on (optional).
                   - task_type: Type of task (optional).
        
        Returns:
            Confirmation message.
        """
        # Validate input structure
        try:
            [PlanStep(**s).model_dump() for s in steps]
            # In a real tool, we might save this to a file or variable.
            # Here, we rely on the PlanHandler to intercept this call and persist it to the DB.
            return "Plan updated successfully."
        except Exception as e:
            return f"Invalid plan format: {str(e)}"

    class Config(BaseModel):
        pass
