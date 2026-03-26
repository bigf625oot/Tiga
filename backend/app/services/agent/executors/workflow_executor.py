import logging
import uuid
from collections import defaultdict, deque
from typing import AsyncGenerator, Dict, Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_model import LLMModel
from app.models.workflow import Workflow
from app.services.agent.schemas.intent import IntentResult
from app.services.agent.executors.base_executor import BaseExecutor
from app.services.agent.components.memory_manager import DefaultMemoryManager
from app.core.i18n import _

logger = logging.getLogger("eah.executors.workflow")


class WorkflowExecutor(BaseExecutor):
    """
    Workflow Executor for static DAG-based workflows.
    Executes workflows via topological sort (Kahn's algorithm) for correct dependency ordering.
    """

    def __init__(
        self,
        llm_model: Optional[LLMModel] = None,
        memory_manager: Optional[DefaultMemoryManager] = None,
        **kwargs
    ):
        super().__init__(llm_model=llm_model, memory_manager=memory_manager, **kwargs)

    async def execute(
        self,
        input_text: str,
        intent: IntentResult,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:

        db: Optional[AsyncSession] = kwargs.get("db")
        session_id = kwargs.get("session_id") or str(uuid.uuid4())

        if not db:
            yield {"type": "error", "content": _("Database session not provided for workflow execution.")}
            return

        try:
            wf = await self._load_workflow(db, intent, kwargs)
            if wf:
                definition = wf.definition or {}
                nodes: List[Dict[str, Any]] = definition.get("nodes") if isinstance(definition, dict) else None

                if not nodes:
                    yield {"type": "error", "content": _("Workflow definition is empty or unsupported.")}
                    return

                yield {"type": "status", "content": _("Executing workflow: {} (v{})").format(wf.name, wf.version)}

                if self.memory_manager:
                    await self.memory_manager.get_compressed_context(session_id, current_query=input_text)

                async for chunk in self._execute_dag(nodes, input_text, session_id, db, kwargs):
                    yield chunk
                return

            # Fallback to SingleExecutor if static workflow is not found
            logger.info("No static workflow config found, falling back to SingleExecutor.")
            yield {"type": "status", "content": _("No workflow found, delegating to task executor.")}
            from app.services.agent.executors.single_executor import SingleExecutor

            fallback_executor = SingleExecutor(
                llm_model=self.llm_model,
                memory_manager=self.memory_manager,
                state_manager=self.state_manager,
                plan_validator=self.plan_validator,
                experience_store=self.experience_store,
                tool_registry=self.tool_registry
            )

            async for chunk in fallback_executor.execute(input_text, intent, **kwargs):
                yield chunk

        except Exception as e:
            logger.error(f"WorkflowExecutor execution failed: {e}", exc_info=True)
            yield {"type": "error", "content": f"Workflow execution failed: {e}"}

    async def _execute_dag(
        self,
        nodes: List[Dict[str, Any]],
        input_text: str,
        session_id: str,
        db: AsyncSession,
        kwargs: Dict[str, Any],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Kahn's topological sort + sequential node execution.
        Node schema: {id, name, type, dependencies: [id, ...], config: {...}}
        Why Kahn's: O(V+E) cycle detection built-in; avoids recursive DFS stack overflow on deep DAGs.
        """
        node_map: Dict[str, Dict[str, Any]] = {str(n["id"]): n for n in nodes}
        in_degree: Dict[str, int] = {nid: 0 for nid in node_map}
        dependents: Dict[str, List[str]] = defaultdict(list)

        for nid, node in node_map.items():
            deps = node.get("dependencies") or []
            in_degree[nid] = len(deps)
            for dep_id in deps:
                dependents[str(dep_id)].append(nid)

        queue: deque = deque(nid for nid, deg in in_degree.items() if deg == 0)
        execution_order: List[str] = []
        node_outputs: Dict[str, str] = {}

        while queue:
            nid = queue.popleft()
            execution_order.append(nid)
            for dependent_nid in dependents[nid]:
                in_degree[dependent_nid] -= 1
                if in_degree[dependent_nid] == 0:
                    queue.append(dependent_nid)

        if len(execution_order) != len(node_map):
            cycle_nodes = [nid for nid, deg in in_degree.items() if deg > 0]
            yield {"type": "error", "content": f"Workflow DAG has circular dependencies involving nodes: {cycle_nodes}"}
            return

        yield {"type": "status", "content": _("DAG parsed: {} nodes in topological order.").format(len(execution_order))}

        for nid in execution_order:
            node = node_map[nid]
            node_name = node.get("name", nid)
            node_type = node.get("type", "task")
            node_config = node.get("config") or {}

            deps = node.get("dependencies") or []
            upstream_context = "\n".join(
                f"[{node_map[str(d)].get('name', d)} output]: {node_outputs.get(str(d), '')}"
                for d in deps if str(d) in node_outputs
            )

            yield {"type": "status", "content": _("Executing node: {} ({})").format(node_name, node_type)}

            try:
                result_text = await self._execute_node(
                    nid=nid,
                    node_name=node_name,
                    node_type=node_type,
                    node_config=node_config,
                    user_input=input_text,
                    upstream_context=upstream_context,
                    db=db,
                    kwargs=kwargs,
                )
                node_outputs[nid] = result_text
                yield {"type": "content", "content": result_text}
            except Exception as e:
                logger.error(f"Node {node_name} ({nid}) failed: {e}", exc_info=True)
                yield {"type": "error", "content": f"Node '{node_name}' failed: {e}"}
                return

    async def _execute_node(
        self,
        nid: str,
        node_name: str,
        node_type: str,
        node_config: Dict[str, Any],
        user_input: str,
        upstream_context: str,
        db: AsyncSession,
        kwargs: Dict[str, Any],
    ) -> str:
        """Dispatch a single DAG node to ExecutionEngine."""
        from app.services.agent.engines.execution_engine import ExecutionEngine
        from app.services.agent.schemas.plan import ExecutionTaskStep

        if not self.llm_model:
            from app.services.platform.llm.resolver import resolve_chat_llm_model
            self.llm_model = await resolve_chat_llm_model(db)

        engine = ExecutionEngine(db=db, tool_registry=self.tool_registry, llm_model=self.llm_model)
        task_step = ExecutionTaskStep(
            task_id=nid,
            title=node_name,
            description=node_config.get("description", node_name),
            dependencies=[],
            executor_role=node_config.get("role", node_type),
            expected_output=node_config.get("expected_output", "Complete successfully"),
        )

        context = [{"role": "system", "content": upstream_context}] if upstream_context else []
        result_parts = []
        async for chunk in engine.execute_task(task_step, context):
            if chunk.get("type") == "content":
                result_parts.append(chunk.get("content", ""))
        return "".join(result_parts)

    async def _load_workflow(self, db: AsyncSession, intent: IntentResult, kwargs: Dict[str, Any]) -> Optional[Workflow]:
        task_params = getattr(intent, "parameters", None) or {}
        params = kwargs.get("params") or {}

        workflow_id = task_params.get("workflow_id") or params.get("workflow_id") or kwargs.get("workflow_id")
        original_id = task_params.get("original_id") or params.get("original_id") or kwargs.get("original_id")
        workflow_name = task_params.get("workflow_name") or params.get("workflow_name") or kwargs.get("workflow_name")
        version = task_params.get("version") or params.get("version") or kwargs.get("version")
        allow_draft = bool(task_params.get("allow_draft") or params.get("allow_draft") or kwargs.get("allow_draft"))

        stmt = None
        if workflow_id:
            stmt = select(Workflow).where(Workflow.id == str(workflow_id))
        elif original_id:
            stmt = select(Workflow).where(Workflow.original_id == str(original_id))
            if version is not None:
                stmt = stmt.where(Workflow.version == int(version))
            else:
                stmt = stmt.where(Workflow.is_latest.is_(True))
        elif workflow_name:
            stmt = select(Workflow).where(Workflow.name == str(workflow_name), Workflow.is_latest.is_(True))

        if stmt is None:
            return None

        if not allow_draft:
            stmt = stmt.where(Workflow.is_draft.is_(False))

        result = await db.execute(stmt)
        return result.scalars().first()
