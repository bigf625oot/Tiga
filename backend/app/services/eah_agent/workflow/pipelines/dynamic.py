import re
import json
import logging
from typing import Any, Dict, List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.eah_agent.workflow.base import EAHWorkflow
from app.services.eah_agent.workflow.schemas.dynamic_flow import DynamicFlowState, WorkflowNode
from app.services.eah_agent.core.agent_manager import agent_manager
from app.services.eah_agent.workflow.helpers import format_workflow_event, persist_workflow_state

logger = logging.getLogger(__name__)

class DynamicWorkflow(EAHWorkflow):
    """
    A workflow engine that executes a dynamic DAG of nodes.
    Supports node types:
    - input: Provides initial variables
    - agent: Executes an Agent or Team
    - tool: Executes a specific Tool (TODO)
    - output: Collects final results
    """
    
    def __init__(self, db: AsyncSession, session_id: str, config: Dict[str, Any]):
        """
        Args:
            config: A dict containing 'nodes' list.
        """
        super().__init__(session_id)
        self.db = db
        
        # Parse nodes from config
        nodes_data = config.get("nodes", [])
        nodes = [WorkflowNode(**n) for n in nodes_data]
        
        self.state = DynamicFlowState(session_id=session_id, nodes=nodes)
        
        # Map for quick lookup
        self.node_map = {n.id: n for n in nodes}
        self.node_outputs = {} # Runtime cache for outputs

    def _topological_sort(self) -> List[WorkflowNode]:
        """
        Compute execution order based on dependencies.
        """
        # Build graph
        graph = {node.id: [] for node in self.state.nodes}
        in_degree = {node.id: 0 for node in self.state.nodes}
        
        for node in self.state.nodes:
            for dep_id in node.inputs:
                if dep_id in graph:
                    graph[dep_id].append(node.id)
                    in_degree[node.id] += 1
        
        # Kahn's Algorithm
        queue = [node.id for node in self.state.nodes if in_degree[node.id] == 0]
        sorted_ids = []
        
        while queue:
            u = queue.pop(0)
            sorted_ids.append(u)
            
            for v in graph[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
                    
        if len(sorted_ids) != len(self.state.nodes):
            raise ValueError("Workflow contains a cycle (circular dependency)")
            
        return [self.node_map[nid] for nid in sorted_ids]

    def _resolve_params(self, params: Any) -> Any:
        """
        Recursively resolve variables in parameters using {{node_id.field}} syntax.
        Example: "Summarize this: {{search_node.output}}"
        """
        if isinstance(params, str):
            # Find all {{...}} patterns
            matches = re.findall(r"\{\{(.*?)\}\}", params)
            result = params
            for match in matches:
                # Parse node_id.field (default field is 'output')
                parts = match.strip().split(".")
                node_id = parts[0]
                field = parts[1] if len(parts) > 1 else "output"
                
                # Get value from outputs
                val = self.node_outputs.get(node_id, {}).get(field, "") if isinstance(self.node_outputs.get(node_id), dict) else self.node_outputs.get(node_id, "")
                
                # Replace in string
                # If the entire string is just the variable, replace with the raw value (to keep types like dict/list)
                if result == f"{{{{{match}}}}}":
                    return val
                
                result = result.replace(f"{{{{{match}}}}}", str(val))
            return result
        elif isinstance(params, dict):
            return {k: self._resolve_params(v) for k, v in params.items()}
        elif isinstance(params, list):
            return [self._resolve_params(v) for v in params]
        return params

    async def _execute_agent_node(self, node: WorkflowNode, params: Dict) -> Any:
        """Execute an Agent node."""
        agent_id = params.get("agent_id")
        team_type = params.get("team_type")
        prompt = params.get("prompt", "")
        
        agent = None
        if team_type:
            # Create a team on the fly
            # Team config should be in params, e.g. {"coordinator_id": "...", ...}
            agent = await agent_manager.create_team(self.db, team_type, params)
        elif agent_id:
            # Create a standard agent
            agent = await agent_manager.create_agno_agent(self.db, agent_id, self.session_id)
        
        if not agent:
            raise ValueError(f"Agent configuration missing for node {node.id}")

        # Run the agent
        # We collect the full response string for now
        response_text = ""
        async for chunk in agent.run(prompt, stream=True):
            if isinstance(chunk, str):
                response_text += chunk
                # Ideally we could yield partials here too, but it complicates the generator structure
        
        return response_text

    async def run_stream(self) -> AsyncGenerator[str, None]:
        """
        Execute the dynamic workflow.
        """
        try:
            sorted_nodes = self._topological_sort()
            self.state.execution_order = [n.id for n in sorted_nodes]
            
            yield format_workflow_event("workflow", "started", "Workflow execution started")
            
            for node in sorted_nodes:
                self.state.current_step = node.id
                yield format_workflow_event(node.id, "running", f"Executing node: {node.name} ({node.type})")
                
                try:
                    # 1. Resolve parameters
                    resolved_params = self._resolve_params(node.params)
                    
                    # 2. Execute logic based on type
                    output = None
                    
                    if node.type == "input":
                        # Input nodes just pass through their params as output
                        output = resolved_params
                        
                    elif node.type == "agent":
                        output = await self._execute_agent_node(node, resolved_params)
                        
                    elif node.type == "tool":
                        # TODO: Implement generic tool execution
                        output = f"Tool execution not implemented yet. Params: {resolved_params}"
                        
                    elif node.type == "output":
                        output = resolved_params
                    
                    # 3. Store result
                    # Ensure output is dict-accessible if needed, or just raw value
                    if isinstance(output, dict):
                        self.node_outputs[node.id] = output
                    else:
                        self.node_outputs[node.id] = {"output": output}
                    
                    # Update state
                    self.state.results[node.id] = self.node_outputs[node.id]
                    self.state.steps_completed.append(node.id)
                    await persist_workflow_state(self.session_id, self.state)
                    
                    yield format_workflow_event(node.id, "completed", output=str(output))
                    
                except Exception as e:
                    logger.exception(f"Error executing node {node.id}")
                    self.state.error = str(e)
                    await persist_workflow_state(self.session_id, self.state)
                    yield format_workflow_event(node.id, "failed", output=str(e))
                    return
            
            yield format_workflow_event("workflow", "finished", "Workflow completed successfully")
            
        except Exception as e:
            logger.exception("Workflow execution failed")
            yield format_workflow_event("workflow", "failed", output=str(e))
