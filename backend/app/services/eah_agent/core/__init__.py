from .agent_manager import AgentManager
from .service import AgentService

__all__ = ["AgentManager", "AgentService", "ExecutorAgent", "PlannerAgent"]


def __getattr__(name: str):
    if name == "ExecutorAgent":
        from .executor import ExecutorAgent

        return ExecutorAgent
    if name == "PlannerAgent":
        from .planner import PlannerAgent

        return PlannerAgent
    raise AttributeError(name)
