from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.lightrag_service import lightrag_service
from app.services.rag_service.models import (
    EmbedRequest, EmbedResponse, SearchRequest, SearchResponse, SearchHit,
    AugmentRequest, AugmentResponse, HealthResponse
)
from app.models.llm_model import LLMModel
from sqlalchemy import select
from app.services.rag_service.providers import OpenAICompatLLM, OpenAIEmbedder, LightRAGVectorStore

class RagService:
    async def embed_documents(self, req: EmbedRequest, db: AsyncSession) -> EmbedResponse:
        await lightrag_service.ensure_initialized(db)
        texts = [it.text for it in req.items]
        res = await db.execute(select(LLMModel).filter(LLMModel.is_active == True, LLMModel.model_type == "embedding").order_by(LLMModel.updated_at.desc()))
        embed_model = res.scalars().first()
        if not embed_model:
            return EmbedResponse(vectors=[])
        embedder = OpenAIEmbedder(api_key=embed_model.api_key, base_url=embed_model.base_url, model=embed_model.model_id)
        vecs = embedder.embed(texts)
        return EmbedResponse(vectors=vecs)

    async def search(self, req: SearchRequest, db: AsyncSession) -> SearchResponse:
        await lightrag_service.ensure_initialized(db)
        store = LightRAGVectorStore()
        refs = store.search(req.query, top_k=req.top_k or 5)
        hits = [SearchHit(title=r.get("title"), score=float(r.get("score") or 0.0), preview=r.get("preview"), url=r.get("url"), page=r.get("page")) for r in refs]
        return SearchResponse(hits=hits)

    async def augment_prompt(self, req: AugmentRequest, db: AsyncSession) -> AugmentResponse:
        await lightrag_service.ensure_initialized(db)
        # assemble prompt with sources
        store = LightRAGVectorStore()
        refs = store.search(req.prompt, top_k=req.top_k or 5)
        knowledge = "\n\n".join([r.get("preview") or "" for r in refs])
        res = await db.execute(select(LLMModel).filter(LLMModel.is_active == True, LLMModel.model_type != "embedding").order_by(LLMModel.updated_at.desc()))
        llm = res.scalars().first()
        if not llm:
            return AugmentResponse(answer="", sources=[])
        client = OpenAICompatLLM(api_key=llm.api_key, base_url=llm.base_url, model=llm.model_id)
        messages = []
        messages.append({"role":"system","content":"你是一个中文知识库助手，仅基于提供的证据回答，若证据不足请明确说明，不要编造。"})
        if req.history:
            messages.append({"role":"system","content":"历史上下文：\n" + "\n".join(req.history)})
        messages.append({"role":"system","content":"证据：\n" + knowledge})
        messages.append({"role":"user","content":req.prompt})
        answer = await client.chat(messages)
        sources = [{"source":"vector","content": r.get("preview") or "", "score": float(r.get("score") or 0.0)} for r in refs][:5]
        return AugmentResponse(answer=answer, sources=sources)

    async def health_check(self, db: AsyncSession) -> HealthResponse:
        llm_model = None
        embed_model = None
        try:
            res = await db.execute(
                select(LLMModel).filter(LLMModel.is_active == True, LLMModel.model_type != "embedding").order_by(LLMModel.updated_at.desc())
            )
            llm_model = res.scalars().first()
            res = await db.execute(
                select(LLMModel).filter(LLMModel.is_active == True, LLMModel.model_type == "embedding").order_by(LLMModel.updated_at.desc())
            )
            embed_model = res.scalars().first()
        except Exception:
            pass
        return HealthResponse(status="ok", llm_model=getattr(llm_model, "model_id", None), embed_model=getattr(embed_model, "model_id", None))

rag_service = RagService()
