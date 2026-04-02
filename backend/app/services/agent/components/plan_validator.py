import logging
from typing import Dict, Any, Tuple, Set, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger("eah.components.validator")

class DefaultPlanValidator:
    """
    Why: 验证执行计划拓扑确定性，剥离沉重 networkx 依赖，自建轻量级环检测。
    """
    def __init__(self, db: Optional[AsyncSession] = None):
        # Why: 预留 db 会话以支持跨会话历史任务约束校验。
        self.db = db

    async def validate(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        tasks = plan.get("tasks", [])
        if not tasks:
            return False, "Plan contains no tasks."

        # Why: 放弃 networkx，避免少量节点规模下引入庞大科学计算库导致的冷启动与内存开销。
        adj_list: Dict[str, List[str]] = {}
        task_ids: Set[str] = set()
        
        for t in tasks:
            tid = str(t.get("task_id", t.get("id", "")))
            if not tid:
                return False, "Task missing required 'id' or 'task_id' field."
            task_ids.add(tid)
            adj_list[tid] = []

        for t in tasks:
            tid = str(t.get("task_id", t.get("id")))
            dependencies = t.get("dependencies", [])
            for dep in dependencies:
                dep_id = str(dep)
                if dep_id not in task_ids:
                    return False, f"Task '{tid}' depends on non-existent task '{dep_id}'."
                adj_list[dep_id].append(tid)

        visited: Dict[str, int] = {tid: 0 for tid in task_ids}
        cycle_path: List[str] = []

        def dfs(node: str) -> bool:
            visited[node] = 1
            cycle_path.append(node)
            
            for neighbor in adj_list.get(node, []):
                if visited[neighbor] == 1:
                    cycle_path.append(neighbor)
                    return True
                elif visited[neighbor] == 0:
                    if dfs(neighbor):
                        return True
                        
            visited[node] = 2
            cycle_path.pop()
            return False

        for node in task_ids:
            if visited[node] == 0:
                if dfs(node):
                    start_idx = cycle_path.index(cycle_path[-1])
                    cycle_str = " -> ".join(cycle_path[start_idx:])
                    return False, f"Cycle detected in task dependencies: {cycle_str}"

        return True, ""
