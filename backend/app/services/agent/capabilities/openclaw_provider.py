import logging
from typing import List, Optional
from agno.tools import Toolkit
from .provider import CapabilityProvider

logger = logging.getLogger(__name__)

class OpenClawCapabilityProvider(CapabilityProvider):
    """
    OpenClaw 分布式任务节点能力提供者
    """
    
    @property
    def provider_type(self) -> str:
        return "openclaw"
        
    async def get_tools(self) -> List[Toolkit]:
        from app.core.config import settings
        
        if not settings.OPENCLAW_BASE_URL:
            return []
            
        try:
            from app.services.ops.openclaw import OpenClawTools
            logger.info("Loaded OpenClawTools")
            return [OpenClawTools()]
        except ImportError:
            logger.warning("OpenClawTools import failed.")
            return []
        except Exception as e:
            logger.error(f"Failed to load OpenClawTools: {e}")
            return []
            
    def get_system_prompt_snippet(self) -> Optional[str]:
        return None
