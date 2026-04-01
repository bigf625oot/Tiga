from __future__ import annotations

from typing import Any, Dict, List

from app.services.ops.pipeline.core.models import DAGNode, DAGPipeline


def build_dag_pipeline_from_config(
    *,
    pipeline_id: str,
    name: str,
    dag_config: Dict[str, Any],
    settings: Dict[str, Any] | None = None,
    description: str | None = None,
) -> DAGPipeline:
    frontend_nodes: List[Dict[str, Any]] = (dag_config or {}).get("nodes", []) or []
    frontend_edges: List[Dict[str, Any]] = (dag_config or {}).get("edges", []) or []

    inputs_map: Dict[str, List[str]] = {}
    for edge in frontend_edges:
        target = edge.get("target")
        source = edge.get("source")
        if not target or not source:
            continue
        inputs_map.setdefault(target, []).append(source)

    backend_nodes: List[DAGNode] = []
    for f_node in frontend_nodes:
        node_id = f_node.get("id")
        if not node_id:
            continue

        node_data = f_node.get("data", {}) or {}
        node_type = f_node.get("type") or node_data.get("type") or "transform"
        if node_type not in {"source", "transform", "sink", "combiner"}:
            node_type = node_data.get("type") or "transform"

        operator = node_data.get("operator") or node_data.get("subType") or "unknown"
        config = node_data.get("config") or {}

        backend_nodes.append(
            DAGNode(
                id=node_id,
                type=node_type,
                operator=operator,
                config=config,
                inputs=inputs_map.get(node_id, []),
                description=node_data.get("label"),
            )
        )

    return DAGPipeline(
        id=pipeline_id,
        name=name,
        nodes=backend_nodes,
        settings=settings or {},
        description=description,
    )

