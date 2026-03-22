from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_knowledge_base import knowledge_base
from app.db.session import get_db
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate
from app.models.knowledge import KnowledgeDocument, DocumentStatus
from sqlalchemy import select, update, delete
from datetime import datetime
import uuid

router = APIRouter()

@router.get("/", response_model=List[KnowledgeBaseResponse])
async def read_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    query: str = None,
) -> Any:
    """
    Retrieve knowledge bases.
    """
    kbs = await knowledge_base.get_multi(db, skip=skip, limit=limit, query=query)
    return kbs

@router.post("/", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    *,
    db: AsyncSession = Depends(get_db),
    kb_in: KnowledgeBaseCreate,
) -> Any:
    """
    Create new knowledge base.
    """
    kb = await knowledge_base.create(db=db, obj_in=kb_in)
    return kb

# Dummy endpoints to prevent frontend 404 errors during UI testing

@router.get("/{id}/files")
async def get_kb_files(id: str, parent_id: str = None, db: AsyncSession = Depends(get_db)):
    # Get all non-deleted files for this KB
    stmt = select(KnowledgeDocument).where(
        KnowledgeDocument.knowledge_base_id == id,
        KnowledgeDocument.is_deleted == False
    )
    result = await db.execute(stmt)
    all_docs = result.scalars().all()
    
    # Build tree structure
    doc_dict = {}
    for doc in all_docs:
        doc_dict[doc.id] = {
            "id": str(doc.id),
            "name": doc.filename,
            "type": "folder" if doc.is_folder else "file",
            "size": doc.file_size,
            "parent_id": str(doc.parent_id) if doc.parent_id else None,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "status": doc.status,
            "authorized_roles": [],
            "authorized_users": [],
            "children": []
        }
        
    # Link children to parents
    root_items = []
    for doc_id, doc_data in doc_dict.items():
        parent_id_val = doc_data["parent_id"]
        if parent_id_val and int(parent_id_val) in doc_dict:
            doc_dict[int(parent_id_val)]["children"].append(doc_data)
        else:
            # If parent_id is specified in request, only return children of that parent
            if parent_id and parent_id_val != parent_id:
                continue
            root_items.append(doc_data)
            
    # If a specific parent_id is requested, find it and return its children
    if parent_id:
        try:
            parent_id_int = int(parent_id)
            if parent_id_int in doc_dict:
                return doc_dict[parent_id_int]["children"]
        except ValueError:
            pass
            
    return root_items

@router.post("/{id}/files")
async def create_kb_file(id: str, data: dict, db: AsyncSession = Depends(get_db)):
    is_folder = data.get("type") == "folder"
    parent_id_val = data.get("parent_id")
    # if parent_id is provided as string, try to parse it to int since model uses Integer
    try:
        parent_id = int(parent_id_val) if parent_id_val else None
    except ValueError:
        parent_id = None

    new_doc = KnowledgeDocument(
        knowledge_base_id=id,
        filename=data.get("name", "New Item"),
        is_folder=is_folder,
        parent_id=parent_id,
        status=DocumentStatus.INDEXED if is_folder else DocumentStatus.UPLOADING,
        file_size=0
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    return {
        "id": str(new_doc.id),
        "name": new_doc.filename,
        "type": "folder" if new_doc.is_folder else "file",
        "parent_id": str(new_doc.parent_id) if new_doc.parent_id else None,
        "created_at": new_doc.created_at.isoformat() if new_doc.created_at else None,
        "authorized_roles": [],
        "authorized_users": []
    }

@router.put("/{id}/files/{file_id}")
async def update_kb_file(id: str, file_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    try:
        file_id_int = int(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID")
        
    doc = await db.get(KnowledgeDocument, file_id_int)
    if not doc or doc.knowledge_base_id != id:
        raise HTTPException(status_code=404, detail="File not found")
        
    if "name" in data:
        doc.filename = data["name"]
    if "parent_id" in data:
        try:
            doc.parent_id = int(data["parent_id"]) if data["parent_id"] else None
        except ValueError:
            pass
            
    await db.commit()
    await db.refresh(doc)
    
    return {
        "id": str(doc.id),
        "name": doc.filename,
        "type": "folder" if doc.is_folder else "file",
        "parent_id": str(doc.parent_id) if doc.parent_id else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "authorized_roles": [],
        "authorized_users": []
    }

@router.delete("/{id}/files/{file_id}")
async def delete_kb_file(id: str, file_id: str, db: AsyncSession = Depends(get_db)):
    try:
        file_id_int = int(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID")
        
    doc = await db.get(KnowledgeDocument, file_id_int)
    if not doc or doc.knowledge_base_id != id:
        raise HTTPException(status_code=404, detail="File not found")
        
    doc.is_deleted = True
    doc.deleted_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "success"}

@router.get("/{id}/config")
async def get_kb_config(id: str):
    return {
        "enable_rag": True,
        "enable_kg": False,
        "chunk_size": 1000,
        "embedding_model": "default",
        "retrieval_strategy": "hybrid",
        "max_file_size": 10,
        "allowed_file_types": [".pdf", ".txt", ".md", ".docx"]
    }

@router.get("/{id}/permissions")
async def get_kb_permissions(id: str):
    return {"roles": [], "users": []}

@router.get("/{id}", response_model=KnowledgeBaseResponse)
async def read_knowledge_base(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
) -> Any:
    """
    Get knowledge base by ID.
    """
    kb = await knowledge_base.get(db=db, id=id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb

@router.put("/{id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
    kb_in: KnowledgeBaseUpdate,
) -> Any:
    """
    Update a knowledge base.
    """
    kb = await knowledge_base.get(db=db, id=id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    kb = await knowledge_base.update(db=db, db_obj=kb, obj_in=kb_in)
    return kb

@router.delete("/{id}")
async def delete_knowledge_base(
    *,
    db: AsyncSession = Depends(get_db),
    id: str,
) -> Any:
    """
    Delete a knowledge base.
    """
    kb = await knowledge_base.get(db=db, id=id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    await knowledge_base.remove(db=db, id=id)
    return {"status": "success"}
