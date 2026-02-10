import logging
import json
from typing import AsyncGenerator, Any, List, Dict
from app.workflow.context import AgentContext
from app.workflow.exceptions import WorkflowStepError
from app.services.agent.manager import agent_manager, has_global_api_key
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.agent import Agent
from app.models.llm_model import LLMModel
from openai import OpenAI
from app.services.agent.tools.runner import run_reasoning_tool_loop
from app.services.agent.tools.duckduckgo import DuckDuckGoTools
from agno.agent import Agent as AgnoAgent
from agno.models.openai import OpenAIChat
from app.services.llm.factory import ModelFactory
from app.core.config import settings

logger = logging.getLogger(__name__)

async def agent_execute_step(context: AgentContext) -> AgentContext:
    """
    Step to execute the agent logic (LLM/Tools).
    """
    try:
        session_id = context.session_id
        agent_id = context.agent_id
        user_msg = context.user_message
        
        agent = None
        agent_obj = None
        
        # 1. Load Agent
        async with AsyncSessionLocal() as db:
            if agent_id:
                try:
                    agent = await agent_manager.create_agno_agent(db, agent_id, session_id)
                    res = await db.execute(select(Agent).filter(Agent.id == agent_id))
                    agent_obj = res.scalars().first()
                except Exception as e:
                    logger.error(f"Failed to load agent {agent_id}: {e}")
                    # If strictly required, raise error. But maybe fallback?
                    # context.error = f"Failed to load agent: {e}"
            
            if not agent:
                 # Fallback logic
                 # Try default active model
                 res = await db.execute(
                    select(LLMModel)
                    .filter(LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
                    .order_by(LLMModel.updated_at.desc())
                 )
                 active_model = res.scalars().first()
                 
                 if active_model:
                     model_instance = ModelFactory.create_model(active_model)
                     is_reasoning = ModelFactory.should_use_agno_reasoning(active_model)
                     agent = AgnoAgent(
                        name="Default Agent",
                        model=model_instance,
                        instructions="You are a helpful assistant.",
                        markdown=True,
                        reasoning=is_reasoning
                     )
                 elif has_global_api_key():
                     agent = AgnoAgent(
                        name="Global Default Agent",
                        model=OpenAIChat(id="gpt-4o", api_key=settings.OPENAI_API_KEY),
                        instructions="You are a helpful assistant.",
                        markdown=True,
                     )
                 else:
                     raise WorkflowStepError("agent_execute_step", "No active agent or model found.")

        # 2. Detect DeepSeek
        deepseek_like = False
        if agent_obj and agent_obj.model_config:
             mid = (agent_obj.model_config.get("model_id") or "").lower()
             if "deepseek" in mid or "reasoner" in mid or "r1" in mid:
                 deepseek_like = True
        
        if not deepseek_like and agent and agent.model:
            mid = (getattr(agent.model, "id", "") or "").lower()
            base = (getattr(agent.model, "base_url", "") or "").lower()
            if "deepseek" in base or "deepseek" in mid or "reasoner" in mid or "r1" in mid:
                deepseek_like = True

        # 3. Prepare History
        # We need to ensure history format is correct for Agno/DeepSeek
        agno_history = []
        for msg in context.history:
             role = msg.get("role")
             content = msg.get("content")
             if not role or not content: continue
             
             msg_dict = {"role": role, "content": content}
             if role == "assistant":
                 # Check for reasoning in meta if available in history dict
                 # context.history is List[Dict], assumed to be simple dicts from DB
                 # If we need reasoning content, we assume it's stored in 'meta_data' or similar if we loaded full objects
                 # But context.history is likely just role/content for LLM context.
                 pass
             agno_history.append(msg_dict)

        # 4. Run Generator
        context.output_stream = _run_agent_generator(agent, user_msg, agno_history, deepseek_like)
        
        return context

    except Exception as e:
        raise WorkflowStepError("agent_execute_step", str(e), e)

async def _run_agent_generator(agent, user_msg, history, is_deepseek):
    try:
        if is_deepseek:
            # DeepSeek Logic
            model_obj = getattr(agent, "model", None)
            api_key = getattr(model_obj, "api_key", None) or ""
            base_url = getattr(model_obj, "base_url", None)
            model_id = getattr(model_obj, "id", None) or "deepseek-reasoner"
            
            # 1. Inject Instructions (Skills/System Prompt)
            if agent.instructions:
                # DeepSeek prefers system prompt at the beginning or as 'system' role
                # We prepend it to history
                history.insert(0, {"role": "system", "content": agent.instructions})

            # 2. Dynamic Tools Loading (Attempt to use agent's configured tools)
            # Default/Fallback tools
            tools = []
            tool_map = {}
            
            # Helper to add default tools if not present
            def add_default_tools():
                ddg = DuckDuckGoTools()
                tools.extend([
                    {
                        "type": "function",
                        "function": {
                            "name": "duckduckgo_search",
                            "description": "Search the web using DuckDuckGo",
                            "parameters": {
                                "type": "object",
                                "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}},
                                "required": ["query"],
                            },
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "get_datetime",
                            "description": "Get current datetime string",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "format": {
                                        "type": "string", 
                                        "description": "Optional format string (e.g. %Y-%m-%d)"
                                    }
                                },
                                "required": [],
                                "additionalProperties": False,
                            },
                        },
                    }
                ])
                
                def _get_datetime(format: str = None):
                    from datetime import datetime
                    if format:
                        try:
                            return {"now": datetime.now().strftime(format)}
                        except:
                            pass
                    return {"now": datetime.now().isoformat()}

                tool_map.update({
                    "duckduckgo_search": lambda query, max_results=5: (
                        ddg.search(query, max_results=max_results) if ddg else '{"error": "ddg not available"}'
                    ),
                    "get_datetime": lambda format=None: _get_datetime(format),
                })

            # Check if agent has tools configured (Agno Agent)
            # Since converting Agno Toolkits to OpenAI schemas dynamically is complex without Agno's internal helpers,
            # We will stick to the default tools for now BUT we have enabled Skills via instructions.
            # TODO: Implement dynamic conversion of agent.tools (including MCP) to OpenAI format.
            add_default_tools()
            
            # Extract tools from Agno Agent (including MCP)
            if agent.tools:
                for toolkit in agent.tools:
                    # 1. Check for MCPToolkit (custom)
                    if hasattr(toolkit, "get_openai_tools") and hasattr(toolkit, "tool_map"):
                        mcp_defs = toolkit.get_openai_tools()
                        tools.extend(mcp_defs)
                        tool_map.update(toolkit.tool_map)
            
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key or "dummy", base_url=base_url)
            
            # Run tool loop directly (async)
            res = await run_reasoning_tool_loop(
                client=client,
                model_id=model_id,
                user_prompt=user_msg,
                tools=tools,
                tool_call_map=tool_map,
                enable_thinking=True,
                messages=history,
            )
            
            final_msg = res["final_message"]
            rc = getattr(final_msg, "reasoning_content", None)
            
            # Yield pseudo-stream
            if rc:
                yield {"type": "reasoning", "content": rc} # We can yield dicts or objects
            
            content = getattr(final_msg, "content", "")
            if content:
                yield {"type": "content", "content": content}
                
        else:
            # Agno Stream
            # agent.run(stream=True) returns a generator of RunResponse
            stream = agent.run(user_msg, stream=True, messages=history)
            for response in stream:
                # response is RunResponse
                # We need to normalize output
                content = ""
                if hasattr(response, "content") and response.content:
                    content = response.content
                elif hasattr(response, "delta") and response.delta:
                    content = response.delta
                
                if content:
                    yield {"type": "content", "content": content}
                    
    except Exception as e:
        logger.error(f"Error in agent generator: {e}")
        yield {"type": "error", "content": str(e)}

