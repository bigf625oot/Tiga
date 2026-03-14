"""
RAG Endpoint
前端接口：
- HTTP POST `/rag/embed/` 接口作用：嵌入文档
- HTTP POST `/rag/search/` 接口作用：搜索文档
- HTTP POST `/rag/augment/` 接口作用：增强提示
- HTTP GET `/rag/health/` 接口作用：健康检查
前端功能：
- 管理和配置RAG系统
- 支持文档嵌入、搜索和增强提示
- 提供系统健康检查
前端文件：
- `app/frontend/src/pages/RAG.vue`
功能模块：
- RAG系统管理
"""



from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.rag.schemas import AugmentRequest, EmbedRequest, SearchRequest
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
