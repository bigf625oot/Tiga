from typing import Dict, List, Any, Optional
import pathway as pw
from app.services.pathway.core.models import DAGPipeline, DAGNode
from app.services.pathway.connectors.source import get_source
from app.services.pathway.connectors.sink import get_sink
from app.services.pathway.operators.registry import OperatorRegistry
from app.services.pathway.core.exceptions import ConfigurationError, PathwayException
from app.core.logger import logger

class DAGParser:
    def __init__(self):
        self.tables: Dict[str, pw.Table] = {}

    def parse(self, pipeline: DAGPipeline) -> None:
        """
        Parse the DAG pipeline and build the Pathway computation graph.
        """
        # 1. Topological Sort or Dependency Resolution
        sorted_nodes = self._topological_sort(pipeline.nodes)
        
        # 2. Build Graph
        for node in sorted_nodes:
            self._process_node(node)

    def _topological_sort(self, nodes: List[DAGNode]) -> List[DAGNode]:
        """
        Sort nodes based on dependencies (inputs).
        """
        node_map = {n.id: n for n in nodes}
        visited = set()
        temp_mark = set()
        sorted_list = []

        def visit(n_id):
            if n_id in temp_mark:
                raise ConfigurationError(f"Cycle detected involving node {n_id}")
            if n_id not in visited:
                temp_mark.add(n_id)
                node = node_map.get(n_id)
                if not node:
                     raise ConfigurationError(f"Node {n_id} not found in pipeline")
                
                for input_id in node.inputs:
                    visit(input_id)
                
                temp_mark.remove(n_id)
                visited.add(n_id)
                sorted_list.append(node)

        for node in nodes:
            if node.id not in visited:
                visit(node.id)
        
        return sorted_list

    def _process_node(self, node: DAGNode):
        """
        Instantiate the Pathway object for a single node.
        """
        logger.info(f"Processing node: {node.id} ({node.type})")
        
        if node.type == "source":
            self._process_source(node)
        elif node.type == "transform":
            self._process_transform(node)
        elif node.type == "sink":
            self._process_sink(node)
        elif node.type == "combiner":
             self._process_combiner(node)
        else:
            raise ConfigurationError(f"Unknown node type: {node.type}")

    def _process_source(self, node: DAGNode):
        source = get_source(node.operator)
        table = source.read(node.config)
        self.tables[node.id] = table

    def _process_transform(self, node: DAGNode):
        if not node.inputs:
            raise ConfigurationError(f"Transform node {node.id} must have at least one input")
        
        # Currently standard transforms take 1 input
        input_table = self.tables.get(node.inputs[0])
        if input_table is None:
            raise ConfigurationError(f"Input table {node.inputs[0]} not found for node {node.id}")

        # Use OperatorRegistry
        op_func = OperatorRegistry.get_operator(node.operator)
        
        # Construct config compatible with operator signature
        # Operators expect (table, config_dict)
        # We pass the node's config as the config dict
        # Note: Some operators might expect "action" in config, usually provided in node.config
        
        # If the operator is "text_process" or similar, node.config should contain "action", "columns", etc.
        result_table = op_func(input_table, node.config)
        self.tables[node.id] = result_table

    def _process_sink(self, node: DAGNode):
        if not node.inputs:
            raise ConfigurationError(f"Sink node {node.id} must have an input")
        
        input_table = self.tables.get(node.inputs[0])
        if input_table is None:
             raise ConfigurationError(f"Input table {node.inputs[0]} not found for node {node.id}")

        sink = get_sink(node.operator)
        sink.write(input_table, node.config)
        # Sinks don't produce a table for downstream (usually), but we can store None or the result if any
        self.tables[node.id] = None 

    def _process_combiner(self, node: DAGNode):
        """
        Handle multi-input nodes like Union or Join.
        """
        if len(node.inputs) < 2:
             raise ConfigurationError(f"Combiner node {node.id} requires at least 2 inputs")

        input_tables = [self.tables[nid] for nid in node.inputs]
        
        if node.operator == "union":
            # pw.Table + pw.Table
            result = input_tables[0]
            for t in input_tables[1:]:
                result += t
            self.tables[node.id] = result

        elif node.operator == "join":
            # pw.Table.join(other, on, how)
            # This is complex as join usually takes 2 tables at a time or we chain them
            # Config should specify join keys
            # For now, implementing simple 2-table join or chaining
            
            left = input_tables[0]
            right = input_tables[1]
            
            on = node.config.get("on") # Column name or list
            how = node.config.get("how", "inner") # inner, outer, left, right
            
            # Pathway join syntax: left.join(right, left.col == right.col, ...)
            # Or simplified: left.join(right, on="col") if supported (Pathway syntax varies)
            # Pathway usually uses `join(other, *conditions)`
            
            # If `on` is a list of columns present in both
            if isinstance(on, list):
                conditions = [left[c] == right[c] for c in on]
                result = left.join(right, *conditions) # simplified
            elif isinstance(on, str):
                result = left.join(right, left[on] == right[on])
            else:
                 # Cross join or error?
                 raise ConfigurationError(f"Join node {node.id} requires 'on' parameter")
                 
            self.tables[node.id] = result
        
        else:
             raise ConfigurationError(f"Unknown combiner operator: {node.operator}")

