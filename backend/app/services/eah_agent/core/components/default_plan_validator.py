import logging
from typing import Dict, Any, Tuple
import networkx as nx


logger = logging.getLogger("eah.components.validator")

class DefaultPlanValidator:
    """
    默认的计划校验器。
    主要验证：
    1. 必须有任务
    2. 任务之间没有循环依赖 (DAG)
    """

    async def validate(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        tasks = plan.get("tasks", [])
        if not tasks:
            return False, "Plan contains no tasks."

        # DAG 循环依赖检查
        dg = nx.DiGraph()
        task_ids = {str(t.get("task_id", t.get("id"))) for t in tasks}
        
        for t in tasks:
            tid = str(t.get("task_id", t.get("id")))
            dg.add_node(tid)
            
            dependencies = t.get("dependencies", [])
            for dep in dependencies:
                dep_id = str(dep)
                if dep_id not in task_ids:
                    return False, f"Task '{tid}' depends on non-existent task '{dep_id}'."
                dg.add_edge(dep_id, tid)

        if not nx.is_directed_acyclic_graph(dg):
            cycle = nx.find_cycle(dg)
            return False, f"Cycle detected in task dependencies: {cycle}"
            
        return True, ""
