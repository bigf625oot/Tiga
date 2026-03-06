import logging
from app.workflow.context import AgentContext
from app.workflow.exceptions import WorkflowStepError
from app.crud.crud_chat import chat as crud_chat
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def persist_step(context: AgentContext) -> AgentContext:
    """
    Step to persist the assistant's response to the database.
    """
    try:
        if not context.final_response:
             logger.warning("No final response to persist.")
             return context

        session_id = context.session_id
        content = context.final_response
        reasoning = context.reasoning_content
        meta = context.meta

        async with AsyncSessionLocal() as db:
             # Save message
             await crud_chat.create_message(
                 db, 
                 session_id, 
                 "assistant", 
                 content, 
                 {"reasoning": reasoning} if reasoning else None
             )
             
             # Save meta
             if meta:
                 await crud_chat.update_message_meta(db, session_id, meta)
        
        return context

    except Exception as e:
        raise WorkflowStepError("persist_step", str(e), e)
