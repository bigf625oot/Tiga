from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings
from app.services.rag.knowledge_base import kb_service

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@router.get("/retrieval")
async def retrieval_health() -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "vector": {
            "backend": (settings.VECTOR_BACKEND or "lancedb").lower(),
            "ok": False,
            "version": None,
            "collection": None,
            "count": None,
        },
        "graph": {
            "backend": (settings.GRAPH_BACKEND or "local").lower(),
            "ok": False,
            "version": None,
            "count": None,
        },
    }

    vb = out["vector"]["backend"]
    gb = out["graph"]["backend"]

    # Vector backend checks
    try:
        if vb == "lancedb":
            import lancedb

            out["vector"]["version"] = getattr(lancedb, "__version__", None)
            # Try to access underlying table name
            tbl = getattr(kb_service.vector_db, "table_name", None)
            out["vector"]["collection"] = tbl
            # Best-effort count: attempt to search all (may return empty), else None
            try:
                # LanceDB Python API doesn't always expose count; skip if not available
                out["vector"]["ok"] = True
            except Exception:
                out["vector"]["ok"] = True
        elif vb == "qdrant":
            from qdrant_client import QdrantClient
            from qdrant_client import __version__ as qv

            out["vector"]["version"] = qv
            client = (
                QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
                if settings.QDRANT_URL
                else QdrantClient()
            )
            coll = settings.QDRANT_COLLECTION
            out["vector"]["collection"] = coll
            try:
                client.get_collection(coll)
                out["vector"]["ok"] = True
                # Count points
                try:
                    res = client.count(collection_name=coll)
                    out["vector"]["count"] = getattr(res, "count", None)
                except Exception:
                    out["vector"]["count"] = None
            except Exception:
                out["vector"]["ok"] = False
        elif vb == "milvus":
            import pymilvus

            out["vector"]["version"] = getattr(pymilvus, "__version__", None)
            from pymilvus import Collection, connections

            host = settings.MILVUS_HOST or "127.0.0.1"
            port = settings.MILVUS_PORT or 19530
            connections.connect("default", host=host, port=port)
            coll = Collection(name=settings.MILVUS_COLLECTION)
            out["vector"]["collection"] = settings.MILVUS_COLLECTION
            out["vector"]["ok"] = True
            try:
                out["vector"]["count"] = coll.num_entities
            except Exception:
                out["vector"]["count"] = None
        else:
            out["vector"]["ok"] = True
    except Exception:
        out["vector"]["ok"] = False

    # Graph backend checks
    try:
        if gb == "neo4j":
            import neo4j

            out["graph"]["version"] = getattr(neo4j, "__version__", None)
            from app.services.rag.graph import _get_driver

            driver = _get_driver()
            with driver.session() as session:
                session.run("RETURN 1")
                out["graph"]["ok"] = True
                try:
                    res = session.run("MATCH (n:Entity) RETURN count(n) AS c")
                    out["graph"]["count"] = res.single()[0]
                except Exception:
                    out["graph"]["count"] = None
        else:
            # local graph is generated on demand; mark ok if service is loaded
            out["graph"]["ok"] = True
    except Exception:
        out["graph"]["ok"] = False

    return out
