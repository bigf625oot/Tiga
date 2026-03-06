import logging
from typing import Any, Dict, List

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_driver():
    try:
        from neo4j import GraphDatabase
    except Exception as e:
        raise RuntimeError("neo4j Python driver not installed") from e
    uri = settings.NEO4J_URI or "bolt://localhost:7687"
    user = settings.NEO4J_USER or "neo4j"
    password = settings.NEO4J_PASSWORD or "password"
    return GraphDatabase.driver(uri, auth=(user, password))


def upsert_graph(doc_id: int, nodes: Dict[str, Any], edges: Dict[str, Any]):
    try:
        driver = _get_driver()
        with driver.session() as session:
            session.execute_write(lambda tx: tx.run("MERGE (d:Doc {doc_id:$doc_id})", doc_id=doc_id))
            for node_id, data in nodes.items():
                name = data.get("name") or node_id
                ntype = data.get("type") or "Entity"
                attrs = data.get("attributes") or {}
                sc = data.get("source_chunks") or []
                if sc and isinstance(sc, list):
                    ids = []
                    previews = []
                    for item in sc:
                        try:
                            ids.append(int(item.get("chunk_id")))
                        except Exception:
                            ids.append(None)
                        previews.append(str(item.get("text") or ""))
                    attrs["source_chunk_ids"] = ids
                    attrs["source_chunk_previews"] = previews
                session.execute_write(
                    lambda tx: tx.run(
                        "MERGE (n:Entity {name:$name, doc_id:$doc_id}) SET n.type=$type, n += $attrs",
                        name=name,
                        doc_id=doc_id,
                        type=ntype,
                        attrs=attrs,
                    )
                )
                if sc and isinstance(sc, list):
                    for item in sc:
                        cid = item.get("chunk_id")
                        prev = item.get("text")
                        session.execute_write(
                            lambda tx: tx.run(
                                "MATCH (d:Doc {doc_id:$doc_id}), (n:Entity {name:$name, doc_id:$doc_id}) "
                                "MERGE (d)-[r:HAS_MENTION {chunk_id:$cid}]->(n) "
                                "SET r.preview=$prev",
                                doc_id=doc_id,
                                name=name,
                                cid=cid,
                                prev=prev,
                            )
                        )
            for edge_id, ed in edges.items():
                src = ed.get("source")
                tgt = ed.get("target")
                label = ed.get("label") or "related"
                if not src or not tgt:
                    continue
                session.execute_write(
                    lambda tx: tx.run(
                        "MATCH (a:Entity {name:$src, doc_id:$doc_id}), (b:Entity {name:$tgt, doc_id:$doc_id}) "
                        "MERGE (a)-[r:REL {label:$label}]->(b)",
                        src=src,
                        tgt=tgt,
                        label=label,
                        doc_id=doc_id,
                        name=name,
                    )
                )
    except Exception as e:
        logger.error(f"Neo4j upsert error: {e}")


def get_document_graph(doc_id: int, limit: int = 200) -> Dict[str, Any]:
    try:
        driver = _get_driver()
        with driver.session() as session:
            result = session.run(
                "MATCH (n:Entity {doc_id:$doc_id}) "
                "OPTIONAL MATCH (n)-[r:REL]->(m:Entity {doc_id:$doc_id}) "
                "RETURN n, r, m LIMIT $limit",
                doc_id=doc_id,
                limit=limit,
            )
            nodes: Dict[str, Any] = {}
            edges: Dict[str, Any] = {}
            for rec in result:
                n = rec["n"]
                r = rec["r"]
                m = rec["m"]
                if n:
                    nid = n.get("name")
                    nodes[nid] = {
                        "name": nid,
                        "type": n.get("type") or "Entity",
                        "attributes": {k: v for k, v in n.items() if k not in ["name", "type", "doc_id"]},
                    }
                if r and m:
                    mid = m.get("name")
                    nodes[mid] = {
                        "name": mid,
                        "type": m.get("type") or "Entity",
                        "attributes": {k: v for k, v in m.items() if k not in ["name", "type", "doc_id"]},
                    }
                    eid = f"{n.get('name')}_{mid}"
                    edges[eid] = {"source": n.get("name"), "target": mid, "label": r.get("label") or "related"}
            dnode = session.run("MATCH (d:Doc {doc_id:$doc_id}) RETURN d", doc_id=doc_id).single()
            if dnode and dnode.get("d"):
                nodes[f"Doc#{doc_id}"] = {"name": f"Doc#{doc_id}", "type": "Doc", "attributes": {"doc_id": doc_id}}
                mentions = session.run(
                    "MATCH (d:Doc {doc_id:$doc_id})-[m:HAS_MENTION]->(n:Entity {doc_id:$doc_id}) RETURN m,n LIMIT $limit",
                    doc_id=doc_id,
                    limit=limit,
                )
                for rec in mentions:
                    m = rec["m"]
                    n = rec["n"]
                    tgt = n.get("name")
                    eid = f"Doc#{doc_id}_MENTION_{tgt}_{m.get('chunk_id')}"
                    edges[eid] = {"source": f"Doc#{doc_id}", "target": tgt, "label": "HAS_MENTION"}
            return {"nodes": nodes, "edges": edges}
    except Exception as e:
        logger.error(f"Neo4j read error: {e}")
        return {"nodes": {}, "edges": {}, "reason": f"error:{str(e)}"}


def search_nodes(doc_id: int, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
    try:
        driver = _get_driver()
        with driver.session() as session:
            res = session.run(
                "MATCH (n:Entity {doc_id:$doc_id}) WHERE toLower(n.name) CONTAINS toLower($q) RETURN n LIMIT $k",
                doc_id=doc_id,
                q=query,
                k=top_k,
            )
            items = []
            for rec in res:
                n = rec["n"]
                name = n.get("name")
                attrs = {k: v for k, v in n.items() if k not in ["name", "type", "doc_id"]}
                items.append({"content": f"实体: {name}\n属性: {attrs}", "score": 1.0, "source": "graph"})
            return items
    except Exception as e:
        logger.error(f"Neo4j search error: {e}")
        return []
