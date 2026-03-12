# Facade for backward compatibility
from app.services.rag.generation.qa import QAService, qa_service

__all__ = ["QAService", "qa_service"]
