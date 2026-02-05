from pathlib import Path
from typing import Dict, Any, Optional
import json
import time
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
import networkx as nx
import logging

logger = logging.getLogger(__name__)

def _default_output_dir() -> Path:
    backend_dir = Path(__file__).resolve().parents[4]
    data_dir = backend_dir / "data"
    out_dir = data_dir / "storage" / "Dataset"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def _graphml_path() -> Path:
    backend_dir = Path(__file__).resolve().parents[4]
    data_dir = backend_dir / "data"
    return data_dir / "lightrag_store" / "graph_chunk_entity_relation.graphml"

def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)

def export_database_to_json(engine: Engine, output_dir: Optional[Path] = None, schema: Optional[str] = None, row_batch_size: int = 1000) -> Dict[str, Any]:
    out_dir = output_dir or _default_output_dir()
    insp = inspect(engine)
    schema_name = schema
    logger.info(f"Exporting database to JSON, schema={schema_name}, out_dir={out_dir}")
    logger.debug(f"SQL dialect={engine.dialect.name}")
    tables = insp.get_table_names(schema=schema_name)
    logger.info(f"Discovered tables count={len(tables)}")
    index = {"generated_at": int(time.time()), "schema": schema_name or "", "tables": []}
    for t in tables:
        cols = insp.get_columns(t, schema=schema_name)
        pks = insp.get_pk_constraint(t, schema=schema_name) or {}
        fks = insp.get_foreign_keys(t, schema=schema_name) or []
        t_slug = _safe_filename(t)
        schema_file = out_dir / f"{t_slug}_schema.json"
        rows_file = out_dir / f"{t_slug}_rows.ndjson"
        logger.debug(f"Writing schema for table={t} to {schema_file}")
        schema_obj = {
            "table": t,
            "schema": schema_name or "",
            "columns": [
                {
                    "name": c.get("name"),
                    "type": str(c.get("type")),
                    "nullable": bool(c.get("nullable")),
                    "default": str(c.get("default")) if c.get("default") is not None else None
                } for c in cols
            ],
            "primary_key": pks.get("constrained_columns") or [],
            "foreign_keys": [
                {
                    "constrained_columns": fk.get("constrained_columns") or [],
                    "referred_schema": fk.get("referred_schema") or "",
                    "referred_table": fk.get("referred_table"),
                    "referred_columns": fk.get("referred_columns") or []
                } for fk in fks
            ]
        }
        with open(schema_file, "w", encoding="utf-8") as sf:
            json.dump(schema_obj, sf, ensure_ascii=False, indent=2)
        index["tables"].append({"table": t, "schema_file": str(schema_file), "rows_file": str(rows_file)})
        dialect = engine.dialect.name
        if schema_name:
            if dialect == "mysql":
                full_name = f"`{schema_name}`.`{t}`"
            elif dialect == "postgresql":
                full_name = f"\"{schema_name}\".\"{t}\""
            else:
                full_name = f"{schema_name}.{t}"
        else:
            if dialect == "mysql":
                full_name = f"`{t}`"
            elif dialect == "postgresql" or dialect == "sqlite":
                full_name = f"\"{t}\""
            else:
                full_name = t
        with engine.connect() as conn, open(rows_file, "w", encoding="utf-8") as rf:
            res = conn.execution_options(stream_results=True).execute(text(f"SELECT * FROM {full_name}"))
            row_count = 0
            while True:
                batch = res.fetchmany(row_batch_size)
                if not batch:
                    break
                for row in batch:
                    m = getattr(row, "_mapping", None)
                    payload = dict(m) if m is not None else dict(row)
                    rf.write(json.dumps(payload, ensure_ascii=False) + "\n")
                row_count += len(batch)
        logger.info(f"Exported table={t}, rows={row_count}, data_file={rows_file}")
    index_file = out_dir / "dataset_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    logger.info(f"Dataset index written to {index_file}")
    return index

def update_graphml_from_dataset(index: Dict[str, Any], graphml_path: Optional[Path] = None):
    g_path = graphml_path or _graphml_path()
    G = None
    if g_path.exists():
        logger.info(f"Reading existing GraphML from {g_path}")
        G = nx.read_graphml(str(g_path))
    else:
        logger.info(f"GraphML not found, creating new graph at {g_path}")
        G = nx.Graph()
    pre_nodes = G.number_of_nodes()
    pre_edges = G.number_of_edges()
    added_nodes = 0
    added_edges = 0
    for t in index.get("tables", []):
        table_name = t["table"]
        schema_file = Path(t["schema_file"])
        with open(schema_file, "r", encoding="utf-8") as sf:
            schema_obj = json.load(sf)
        table_node_id = f"db:table:{table_name}"
        if table_node_id not in G:
            G.add_node(table_node_id, entity_type="DBTable", table_name=table_name, schema=index.get("schema", ""), columns_count=len(schema_obj.get("columns", [])))
            added_nodes += 1
        for col in schema_obj.get("columns", []):
            col_node_id = f"db:column:{table_name}.{col['name']}"
            if col_node_id not in G:
                G.add_node(col_node_id, entity_type="DBColumn", table=table_name, column_name=col["name"], data_type=col["type"], nullable=str(col["nullable"]), default=str(col["default"]) if col["default"] is not None else "")
                added_nodes += 1
            if not G.has_edge(table_node_id, col_node_id):
                G.add_edge(table_node_id, col_node_id, description="has_column")
                added_edges += 1
        for fk in schema_obj.get("foreign_keys", []):
            src_cols = fk.get("constrained_columns") or []
            ref_table = fk.get("referred_table")
            ref_cols = fk.get("referred_columns") or []
            for sc in src_cols:
                src_id = f"db:column:{table_name}.{sc}"
                for rc in ref_cols:
                    tgt_id = f"db:column:{ref_table}.{rc}"
                    if src_id in G and tgt_id in G and not G.has_edge(src_id, tgt_id):
                        G.add_edge(src_id, tgt_id, description=f"fk:{table_name}.{sc}->{ref_table}.{rc}")
                        added_edges += 1
    nx.write_graphml(G, str(g_path))
    logger.info(f"GraphML updated path={g_path}, nodes={G.number_of_nodes()}(+{added_nodes}), edges={G.number_of_edges()}(+{added_edges}), prev_nodes={pre_nodes}, prev_edges={pre_edges}")
    return str(g_path)

def get_db_graph_stats(graphml_path: Optional[Path] = None) -> Dict[str, Any]:
    g_path = graphml_path or _graphml_path()
    if not g_path.exists():
        return {"exists": False, "path": str(g_path), "nodes": 0, "edges": 0, "db_tables": 0, "db_columns": 0, "has_column_edges": 0, "fk_edges": 0, "tables": []}
    G = nx.read_graphml(str(g_path))
    total_nodes = G.number_of_nodes()
    total_edges = G.number_of_edges()
    db_tables = 0
    db_columns = 0
    has_column_edges = 0
    fk_edges = 0
    tables = []
    for nid, data in G.nodes(data=True):
        et = str(data.get("entity_type") or "")
        if et == "DBTable" or str(nid).startswith("db:table:"):
            db_tables += 1
            name = data.get("table_name") or str(nid).replace("db:table:", "")
            if name:
                tables.append(str(name))
        elif et == "DBColumn" or str(nid).startswith("db:column:"):
            db_columns += 1
    for u, v, edata in G.edges(data=True):
        desc = str(edata.get("description") or "")
        if desc == "has_column":
            has_column_edges += 1
        elif desc.startswith("fk:"):
            fk_edges += 1
    tables = sorted(list(set(tables)))
    return {
        "exists": True,
        "path": str(g_path),
        "nodes": total_nodes,
        "edges": total_edges,
        "db_tables": db_tables,
        "db_columns": db_columns,
        "has_column_edges": has_column_edges,
        "fk_edges": fk_edges,
        "tables": tables[:50]
    }
