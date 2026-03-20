__all__ = [
    "AgentService",
    "agent_service",
    "ExecutorAgent",
    "PlannerAgent",
    "AgnoControlPlane",
    "NluService",
    "IntentResult",
    "IntentType",
]


def __getattr__(name: str):
    if name == "AgentService":
        from .agent_service import AgentService
        return AgentService
    if name == "agent_service":
        from .agent_service import agent_service
        return agent_service
    if name == "ExecutorAgent":
        from .agent_executor import ExecutorAgent
        return ExecutorAgent
    if name == "PlannerAgent":
        from .agent_planner import PlannerAgent
        return PlannerAgent
    if name == "AgnoControlPlane":
        from .agent_control_plane import AgnoControlPlane
        return AgnoControlPlane
    if name == "NluService":
        from .agent_nlu import NluService
        return NluService
    if name == "IntentResult":
        from .agent_nlu import IntentResult
        return IntentResult
    if name == "IntentType":
        from .agent_nlu import IntentType
        return IntentType
    raise AttributeError(name)
