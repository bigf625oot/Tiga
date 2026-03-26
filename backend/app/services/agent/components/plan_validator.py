import logging
from typing import Dict, Any, Tuple, Set, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger("eah.components.validator")

class DefaultPlanValidator:
    """
    Plan Validator: 生产级任务计划校验器
    - 检查任务是否有循环依赖 (基于轻量级拓扑排序，剥离沉重的 networkx 依赖)
    - 检查任务是否引用了不存在的任务
    - 验证输入结构的确定性
    """
    def __init__(self, db: Optional[AsyncSession] = None):
        # 预留数据库会话，未来如果需要跨会话读取历史任务约束时使用
        self.db = db

    async def validate(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        tasks = plan.get("tasks", [])
        if not tasks:
            return False, "Plan contains no tasks."

        # P10: 构建轻量级邻接表 (Adjacency List)
        # Why: 放弃 networkx。对于 Agent 生成的少量任务 (通常 < 20)，
        # 引入庞大的第三方科学计算库会严重拖慢启动速度，并增加包体积和内存开销。
        adj_list: Dict[str, List[str]] = {}
        task_ids: Set[str] = set()
        
        # 第一遍：收集所有合法的 Task ID
        for t in tasks:
            tid = str(t.get("task_id", t.get("id", "")))
            if not tid:
                return False, "Task missing required 'id' or 'task_id' field."
            task_ids.add(tid)
            adj_list[tid] = []

        # 第二遍：构建依赖关系并检查孤儿引用
        for t in tasks:
            tid = str(t.get("task_id", t.get("id")))
            dependencies = t.get("dependencies", [])
            for dep in dependencies:
                dep_id = str(dep)
                if dep_id not in task_ids:
                    return False, f"Task '{tid}' depends on non-existent task '{dep_id}'."
                # 记录有向边：依赖节点 -> 当前节点
                adj_list[dep_id].append(tid)

        # 第三遍：使用 DFS 检测环 (Cycle Detection)
        # 0 = 未访问, 1 = 正在访问, 2 = 已访问
        visited: Dict[str, int] = {tid: 0 for tid in task_ids}
        cycle_path: List[str] = []

        def dfs(node: str) -> bool:
            """如果检测到环返回 True"""
            visited[node] = 1
            cycle_path.append(node)
            
            for neighbor in adj_list.get(node, []):
                if visited[neighbor] == 1:
                    # 发现反向边，说明成环
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
                    # 截取成环的部分用于报错提示
                    start_idx = cycle_path.index(cycle_path[-1])
                    cycle_str = " -> ".join(cycle_path[start_idx:])
                    return False, f"Cycle detected in task dependencies: {cycle_str}"

        return True, ""
