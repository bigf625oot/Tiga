from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.relation_fix_service import relation_fix_service

router = APIRouter()

class DetectRequest(BaseModel):
    main_node: str
    keyword: str

class FixRequest(BaseModel):
    source: str
    target: str
    description: Optional[str] = None
    keywords: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = {}

class BatchFixRequest(BaseModel):
    fixes: List[FixRequest]

class CreateRelationRequest(BaseModel):
    source: str
    target: str
    rel_type: str
    attributes: Optional[Dict[str, Any]] = {}

class DeleteRelationItem(BaseModel):
    source: str
    target: str

class DeleteRelationsRequest(BaseModel):
    relations: List[DeleteRelationItem]

class RestoreRequest(BaseModel):
    filename: Optional[str] = None

@router.post("/detect", response_model=List[Dict[str, Any]])
def detect_relations(request: DetectRequest):
    """
    Detect missing relations based on keyword matching.
    """
    return relation_fix_service.detect_relations(request.main_node, request.keyword)

@router.post("/fix", response_model=Dict[str, int])
def apply_fixes(request: BatchFixRequest):
    """
    Apply a batch of relation fixes.
    """
    count = relation_fix_service.apply_fix([fix.dict() for fix in request.fixes])
    return {"count": count}

@router.post("/create", response_model=Dict[str, bool])
def create_relation(request: CreateRelationRequest):
    """
    Create a single new relation between two nodes.
    """
    success = relation_fix_service.create_relation(
        request.source, request.target, request.rel_type, request.attributes
    )
    return {"success": success}

@router.post("/delete", response_model=Dict[str, int])
def delete_relations(request: DeleteRelationsRequest):
    """
    Delete a batch of relations.
    """
    count = relation_fix_service.delete_relations(
        [rel.dict() for rel in request.relations]
    )
    return {"count": count}

@router.post("/backup", response_model=Dict[str, str])
def backup_graph():
    """
    Create a backup of the current graph file.
    """
    path = relation_fix_service.backup_graph()
    return {"path": path}

@router.post("/restore", response_model=Dict[str, bool])
def restore_backup(request: RestoreRequest):
    """
    Restore the graph from a backup file. If filename is not provided, restores the latest backup.
    """
    success = relation_fix_service.restore_backup(request.filename)
    return {"success": success}

@router.get("/logs", response_model=List[str])
def get_logs(limit: int = 100):
    """
    Get operation logs.
    """
    return relation_fix_service.get_logs(limit)

@router.get("/search", response_model=List[str])
def search_nodes(q: str = Query(..., description="Query string for node name"), limit: int = 20):
    """
    Search for nodes by name.
    """
    return relation_fix_service.search_nodes(q, limit)

@router.get("/node/{node_id}", response_model=Dict[str, Any])
def get_node_relations(node_id: str):
    """
    Get a node and its immediate relations (for visualization).
    """
    return relation_fix_service.get_node_relations(node_id)
