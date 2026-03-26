"""
Health Check Endpoint
前端接口：
- HTTP GET `/health/` 接口作用：检查应用健康状态
- HTTP GET `/health/retrieval` 接口作用：检查检索系统健康状态
前端功能：
- 提供应用和检索系统的健康状态检查
- 支持不同类型的健康检查（如数据库连接、服务可用性等）
前端文件：
- `app/frontend/src/pages/Health.vue`
功能模块：
- 健康状态检查
"""
from typing import Any, Dict
import time
import asyncio

from fastapi import APIRouter

from app.core.config import settings
from app.services.intelligence.knowledge.rag.knowledge_base import kb_service   

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    return {"status": "ok", "ts": int(time.time())}


def _check_qdrant(url, api_key, coll):
    from qdrant_client import QdrantClient
    client = QdrantClient(url=url, api_key=api_key) if url else QdrantClient()
    client.get_collection(coll)
    try:
        return getattr(client.count(collection_name=coll), "count", None)
    except Exception:
        return None

def _check_milvus(host, port, coll_name):
    from pymilvus import Collection, connections
    connections.connect("default", host=host, port=port)
    coll = Collection(name=coll_name)
    try:
        return coll.num_entities
    except Exception:
        return None

def _check_neo4j():
    from app.services.intelligence.knowledge.rag.graph import _get_driver
    driver = _get_driver()
    with driver.session() as session:
        session.run("RETURN 1")
        try:
            res = session.run("MATCH (n:Entity) RETURN count(n) AS c")
            return res.single()[0]
        except Exception:
            return None

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
            out["vector"]["ok"] = True
        elif vb == "qdrant":
            from qdrant_client import __version__ as qv
            out["vector"]["version"] = qv
            coll = settings.QDRANT_COLLECTION
            out["vector"]["collection"] = coll
            try:
                count = await asyncio.to_thread(_check_qdrant, settings.QDRANT_URL, settings.QDRANT_API_KEY, coll)
                out["vector"]["ok"] = True
                out["vector"]["count"] = count
            except Exception:
                out["vector"]["ok"] = False
        elif vb == "milvus":
            import pymilvus
            out["vector"]["version"] = getattr(pymilvus, "__version__", None)   
            host = settings.MILVUS_HOST or "127.0.0.1"
            port = settings.MILVUS_PORT or 19530
            out["vector"]["collection"] = settings.MILVUS_COLLECTION
            try:
                count = await asyncio.to_thread(_check_milvus, host, port, settings.MILVUS_COLLECTION)
                out["vector"]["ok"] = True
                out["vector"]["count"] = count
            except Exception:
                out["vector"]["ok"] = False
        else:
            out["vector"]["ok"] = True
    except Exception:
        out["vector"]["ok"] = False

    # Graph backend checks
    try:
        if gb == "neo4j":
            import neo4j
            out["graph"]["version"] = getattr(neo4j, "__version__", None)       
            try:
                count = await asyncio.to_thread(_check_neo4j)
                out["graph"]["ok"] = True
                out["graph"]["count"] = count
            except Exception:
                out["graph"]["ok"] = False
        else:
            out["graph"]["ok"] = True
    except Exception:
        out["graph"]["ok"] = False

    return out
