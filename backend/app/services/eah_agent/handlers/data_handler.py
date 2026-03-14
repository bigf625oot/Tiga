import logging
import json
from typing import AsyncGenerator, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.core.base_handler import BaseHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.models.llm_model import LLMModel
from app.core.i18n import _

# Import legacy services for now, to be refactored later into tools
from app.services.rag.kg_query import KGQueryService
from app.services.chatbi.vanna.service import data_query_service

logger = logging.getLogger(__name__)

class DataHandler(BaseHandler):
    """
    Handles 'data_query' (SQL) and 'kg_qa' (Knowledge Graph) intents.
    Wraps existing specialized services.
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)
        self.kg_service = KGQueryService.get_instance()
        # data_query_service is a global instance

    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        db = kwargs.get("db")
        
        try:
            if intent.intent == "kg_qa":
                yield {"type": "status", "content": _("Querying Knowledge Graph...")}
                
                # Use KG Service
                # Note: KG service might not support streaming in the same way, adapting
                chart_config = await self.kg_service.generate_chart(input_text)
                
                if chart_config:
                    yield {"type": "content", "content": _("I found some relationships in the Knowledge Graph:\n")}
                    # Send chart data
                    # Frontend expects specific event or we embed it?
                    # ControlPlane maps 'content' to 'text'. We might need a 'chart' type.
                    yield {"type": "chart", "content": chart_config}
                else:
                    yield {"type": "content", "content": _("I searched the Knowledge Graph but found no specific data matching your query.")}
                    
            elif intent.intent == "data_query":
                yield {"type": "status", "content": _("Querying Database (Text-to-SQL)...")}
                
                # Use Vanna Service (Streaming)
                # Pass session_id=None to avoid legacy logging if needed, or handle it
                dq_generator = data_query_service.query(input_text, session_id=None)
                
                async for chunk in dq_generator:
                    try:
                        # chunk is JSON string: {"type":..., "content":...}
                        obj = json.loads(chunk)
                        msg_type = obj.get("type")
                        content = obj.get("content")
                        
                        if msg_type == "process":
                            yield {"type": "think", "content": content + "\n"}
                        elif msg_type == "sql":
                            # Wrap SQL
                            yield {"type": "content", "content": f"\n```sql\n{content}\n```\n"}
                        elif msg_type == "data":
                            yield {"type": "content", "content": content}
                        elif msg_type == "chart":
                             # Handle chart extraction if needed
                             import re
                             match = re.search(r'::: echarts([\s\S]*?):::', content)
                             if match:
                                 chart_json = json.loads(match.group(1).strip())
                                 yield {"type": "chart", "content": chart_json}
                             else:
                                 yield {"type": "content", "content": content}
                        elif msg_type == "error":
                            yield {"type": "error", "content": content}
                        else:
                            yield {"type": "content", "content": content}
                            
                    except json.JSONDecodeError:
                        continue
                        
            else:
                yield {"type": "error", "content": _("Unknown data intent.")}

        except Exception as e:
            logger.error(f"DataHandler failed: {e}")
            yield {"type": "error", "content": _("I encountered an error while querying data.")}
