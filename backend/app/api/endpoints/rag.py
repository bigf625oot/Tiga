from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.rag.models import AugmentRequest, EmbedRequest, SearchRequest
from app.services.rag.service import rag_service

router = APIRouter()


@router.post("/embed")
async def embed_documents(req: EmbedRequest, db: AsyncSession = Depends(get_db)):
    return await rag_service.embed_documents(req, db)


@router.post("/search")
async def search(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    return await rag_service.search(req, db)


@router.post("/augment")
async def augment(req: AugmentRequest, db: AsyncSession = Depends(get_db)):
    return await rag_service.augment_prompt(req, db)


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    return await rag_service.health_check(db)
