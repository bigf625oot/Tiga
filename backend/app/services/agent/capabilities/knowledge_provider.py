import logging
from typing import List, Dict, Any, Optional
from agno.tools import Toolkit
from .provider import CapabilityProvider

logger = logging.getLogger(__name__)

class KnowledgeCapabilityProvider(CapabilityProvider):
    """
    知识库能力提供者：RAG 工具
    """
    
    def __init__(self, knowledge_config: Any):
        self.knowledge_config = knowledge_config
        
    @property
    def provider_type(self) -> str:
        return "knowledge"
        
    async def get_tools(self) -> List[Toolkit]:
        has_documents = False
        if self.knowledge_config and isinstance(self.knowledge_config, dict):
            has_documents = bool(self.knowledge_config.get("document_ids"))
            
        if not (self.knowledge_config or has_documents):
            return []
            
        try:
            from app.services.intelligence.knowledge.rag.mcp_server import search_knowledge_base, query_knowledge_graph
            logger.info("Loaded Knowledge Base Tools")
            return [search_knowledge_base, query_knowledge_graph]
        except ImportError:
            logger.warning("Knowledge Base Tools requested but import failed.")
            return []
            
    def get_system_prompt_snippet(self) -> Optional[str]:
        return None
