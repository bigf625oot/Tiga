import logging
from typing import Optional, List
from app.workflow.context import AgentContext
from app.workflow.exceptions import WorkflowStepError
from app.services.rag.knowledge_base import kb_service
from app.models.knowledge import KnowledgeDocument
from sqlalchemy import select
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def rag_retrieve_step(context: AgentContext) -> AgentContext:
    """
    Step to retrieve documents from Knowledge Base.
    """
    try:
        if not context.doc_ids:
            logger.info("No doc_ids in context, skipping retrieval.")
            return context

        logger.info(f"Starting retrieval for doc_ids: {context.doc_ids}")
        
        # Logic from chat.py
        allowed_names = []
        async with AsyncSessionLocal() as db:
             docs_res = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id.in_(context.doc_ids)))
             docs = docs_res.scalars().all()
             allowed_names = [d.filename for d in docs if d and d.filename]

        # Strict mode check (can be added to context if needed)
        strict_enabled = context.meta.get("strict_mode", False)
        
        references = []
        filtered_out = []

        try:
            if hasattr(kb_service, "search"):
                # kb_service.search is likely synchronous or needs running in thread
                import asyncio
                refs, filtered = await asyncio.to_thread(
                    kb_service.search,
                    query=context.user_message,
                    allowed_names=allowed_names if strict_enabled else None,
                    min_score=context.meta.get("threshold", 0.85),
                    top_k=5,
                )
                references = refs or []
                filtered_out = filtered or []
        except Exception as se:
            logger.warning(f"Retrieval failed: {se}")
            # We don't necessarily fail the workflow if retrieval fails, just log it?
            # Or should we throw WorkflowStepError? 
            # For now, let's treat it as non-fatal but log it.
        
        context.retrieved_references = references
        if filtered_out:
            context.meta["filtered_out"] = filtered_out
            
        return context

    except Exception as e:
        raise WorkflowStepError("rag_retrieve_step", str(e), e)
