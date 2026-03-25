# Facade for backward compatibility
from app.services.rag.knowledge.service import KnowledgeBaseService, kb_service
from app.services.rag.config.settings import UPLOAD_DIR

__all__ = ["KnowledgeBaseService", "kb_service", "UPLOAD_DIR"]
