import json
import inspect
from typing import List, Optional, AsyncGenerator, Any, Dict
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import logger
from app.crud.crud_chat import chat as crud_chat
from app.models.agent import Agent
from app.models.llm_model import LLMModel
from app.models.knowledge import KnowledgeDocument
from app.services.eah_agent.core.agent_manager import agent_manager
from app.services.llm.factory import ModelFactory
from app.services.rag.knowledge_base import kb_service
from app.core.config import settings
from agno.agent import Agent as AgnoAgent
from agno.models.openai import OpenAIChat
from openai import OpenAI
from app.services.eah_agent.tools.libs.duckduckgo import DuckDuckGoTools
from app.services.eah_agent.tools.libs.runner import run_reasoning_tool_loop
from app.core.agent_pool import agent_pool
from app.services.eah_agent.core.stream_processor import parse_thinking_stream
from datetime import datetime
from app.services.nlu.classifier import IntentClassifier, QueryIntent
from app.services.rag.kg_query import KGQueryService
from app.services.chatbi.vanna.service import data_query_service
from app.core.shared_state import StateManager, SharedState, AgentConfig

# Initialize Services
kg_query_service = KGQueryService.get_instance()
intent_classifier = IntentClassifier.get_instance()

class ChatService:
    def _format_sse(self, event: str, data: Any) -> str:
        """Format data as Server-Sent Event"""
        payload = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {payload}\n\n"

    async def process_chat(
        self,
        session_id: str,
        message: str,
        db: AsyncSession,
        enable_search: bool = True,
        strict_mode: bool = False,
        threshold: float = 0.85,
        debug: bool = False,
        ab_variant: Optional[str] = None,
        attachments: Optional[List[int]] = None
    ) -> AsyncGenerator[str, None]:
        try:
            # 1. Get Session
            logger.info(f"[CHAT] Starting chat for session={session_id}")
            session = await crud_chat.get(db, session_id)
            if not session:
                logger.error(f"[CHAT] Session {session_id} not found")
                yield self._format_sse("error", "Session not found")
                return

            # [New] State Management
            state_manager = StateManager.get_instance()
            shared_state = await state_manager.get_state(session_id)
            if not shared_state:
                shared_state = SharedState(session_id=session_id, mode=session.mode if session else "chat")
                await state_manager.save_state(session_id, shared_state)
            
            if session and session.mode != shared_state.mode:
                await state_manager.update_mode(session_id, session.mode)
                # Refresh local state object
                shared_state = await state_manager.get_state(session_id)

            # 2. Save User Message
            logger.debug(f"[CHAT] User message: {message[:50]}...")
            user_msg = await crud_chat.create_message(db, session_id, "user", message)

            # [New] Unified Search Logic
            should_use_classifier = (session.mode == "chat") and (not strict_mode)
            
            if should_use_classifier:
                # Classify Intent
                intent = await intent_classifier.classify(message)
                logger.info(f"[CHAT] Intent classified as: {intent}")
                
                # Intelligent Query Mode (SQL or KG)
                if intent == QueryIntent.KG_QUERY or intent == QueryIntent.STRUCTURED_QUERY or intent == QueryIntent.SQL_QUERY:
                    # Route to Data/KG Engine
                    yield self._format_sse("think", f"Identified intent {intent}. Routing to Data Engine...\n")
                    
                    try:
                        # 1. Knowledge Graph Query
                        if intent == QueryIntent.KG_QUERY:
                            chart_config = await kg_query_service.generate_chart(message)
                            if chart_config:
                                yield self._format_sse("text", "I have generated a visualization based on the Knowledge Graph data:\n")
                                yield self._format_sse("chart", chart_config)
                                
                                # Save as assistant message
                                await self._save_assistant_message(db, session_id, "Generated Chart", {"chart": chart_config, "intent": intent})
                                yield self._format_sse("done", "[DONE]")
                                return
                            else:
                                yield self._format_sse("think", "I searched the Knowledge Graph but found no matching data. Falling back to document search...\n")
                        
                        # 2. Structured SQL Query (Smart Data)
                        elif intent == QueryIntent.STRUCTURED_QUERY or intent == QueryIntent.SQL_QUERY:
                            yield self._format_sse("think", "I noticed you are asking for specific data. Checking database...\n")
                            
                            # Send Meta event for Intelligent Query UI
                            yield self._format_sse("meta", {"msg_type": "intelligent_query"})
                            
                            # Stream from Data Query Service (Vanna)
                            # We pass session_id=None to avoid data_query_service saving the message to the wrong table (DataQueryMessage)
                            # We will save it manually to ChatMessage table later.
                            dq_generator = data_query_service.query(message, session_id=None)
                            
                            full_content = ""
                            generated_sql = None
                            chart_config = None
                            
                            async for chunk in dq_generator:
                                try:
                                    # chunk is a JSON string line: {"step":..., "content":..., "type":...}
                                    obj = json.loads(chunk)
                                    content = obj.get("content")
                                    b_type = obj.get("type")
                                    
                                    # Map backend type to ChatService SSE event
                                    if b_type == "process":
                                        yield self._format_sse("think", content)
                                    elif b_type == "error":
                                        yield self._format_sse("error", content)
                                        full_content += f"\nError: {content}\n"
                                    elif b_type == "sql":
                                        # SQL is sent as special text block or meta
                                        generated_sql = content.replace("```sql\n", "").replace("\n```", "").strip()
                                        sql_block = f"\n```sql\n{generated_sql}\n```\n"
                                        yield self._format_sse("text", sql_block)
                                        full_content += sql_block
                                    elif b_type == "data":
                                        # Table data (markdown)
                                        yield self._format_sse("text", content)
                                        full_content += content
                                    elif b_type == "chart":
                                        # Chart block "::: echarts ..."
                                        # Extract JSON
                                        import re
                                        match = re.search(r'::: echarts([\s\S]*?):::', content)
                                        if match:
                                            try:
                                                chart_json = json.loads(match.group(1).strip())
                                                chart_config = chart_json
                                                yield self._format_sse("chart", chart_json)
                                                # Append echarts block to full_content for persistence
                                                full_content += f"\n::: echarts\n{json.dumps(chart_json, ensure_ascii=False)}\n:::\n"
                                            except:
                                                yield self._format_sse("text", content)
                                                full_content += content
                                        else:
                                            yield self._format_sse("text", content)
                                            full_content += content
                                    else:
                                        # Normal text
                                        yield self._format_sse("text", content)
                                        full_content += content
                                        
                                except json.JSONDecodeError:
                                    pass
                                except Exception as e:
                                    logger.error(f"Error parsing data query chunk: {e}")
                            
                            # Save final message with SQL and Chart metadata
                            meta = {
                                "intent": intent,
                                "sql_query": generated_sql,
                                "chart_config": chart_config,
                                "msg_type": "intelligent_query"
                            }
                            # Save manually as we bypassed data_query_service's internal save
                            await self._save_assistant_message(db, session_id, full_content, meta)
                            
                            yield self._format_sse("done", "[DONE]")
                            return

                    except Exception as e:
                        logger.error(f"[CHAT] Data Engine failed: {e}")
                        yield self._format_sse("think", f"Data query failed: {e}. Falling back to documents...\n")

            # ... Continue with existing Agent/RAG flow (Lines 53+) ...
            # 3. Initialize Agent (with Cache)
            agent = None
            agent_obj = None
            target_agent_runner = None
            fallback_agent_runner = None
            deepseek_like = False
            
            cache_key = f"{session_id}:{session.mode if session else 'chat'}"
            cached_data = agent_pool.get(cache_key)
            
            if cached_data:
                agent, agent_obj, deepseek_like = cached_data
                logger.info(f"[CHAT] Used cached agent for {session_id}")
            else:
                if session.agent_id:
                    agent, agent_obj = await self._load_agent(db, session.agent_id, session_id, enable_search)
                    if agent:
                        deepseek_like = self._detect_deepseek(agent, agent_obj)
                else:
                    agent, agent_obj, deepseek_like = await self._create_default_agent(
                        db, session_id, message, user_msg, enable_search, session.mode
                    )
                
                if agent:
                    # Save Agent Config to SharedState
                    try:
                        mid = ""
                        if hasattr(agent.model, "id"): mid = agent.model.id
                        elif hasattr(agent.model, "model_id"): mid = agent.model.model_id
                        
                        inst = getattr(agent, "instructions", "")
                        if isinstance(inst, list): inst = "\n".join(inst)
                        
                        tool_names = []
                        if agent.tools:
                             for t in agent.tools:
                                 if hasattr(t, "name"): tool_names.append(t.name)
                                 elif hasattr(t, "__name__"): tool_names.append(t.__name__)
                        
                        if shared_state:
                             shared_state.agent_config = AgentConfig(
                                 model_id=str(mid),
                                 instructions=str(inst),
                                 tools=tool_names
                             )
                             await state_manager.save_state(session_id, shared_state)
                    except Exception as e:
                        logger.warning(f"Failed to save agent config to shared state: {e}")

                    agent_pool.put(cache_key, (agent, agent_obj, deepseek_like))
            
            if not agent:
                 yield self._format_sse("error", "Failed to initialize agent.")
                 return

            # 4. Build History & Runners
            agno_history = await self._build_history(db, session_id, user_msg, deepseek_like)
            
            if deepseek_like:
                target_agent_runner = None # Use deepseek loop
            else:
                async def _standard_runner():
                    return await agent.arun(message, stream=True, stream_events=True, messages=agno_history)
                
                async def _fallback_runner():
                    res = await agent.arun(message, stream=False, messages=agno_history)
                    return [res]
                
                target_agent_runner = _standard_runner
                fallback_agent_runner = _fallback_runner

            # 5. RAG Retrieval (Optional)
            references = []
            structured_refs = []
            filtered_out = []
            retrieval_note = None
            
            allowed_names, strict_enabled = await self._get_allowed_docs(db, agent_obj, attachments, strict_mode)
            
            if strict_enabled and allowed_names:
                retrieval_note = "根据绑定文档检索"

            try:
                if hasattr(kb_service, "search"):
                    import asyncio
                    refs, filtered = await asyncio.to_thread(
                        kb_service.search,
                        query=message,
                        allowed_names=allowed_names if strict_enabled else None,
                        min_score=threshold,
                        top_k=5,
                    )
                    references = refs or []
                    filtered_out = filtered or []
                    structured_refs = await self._build_structured_refs(db, references)
            except Exception as se:
                logger.warning(f"Retrieval failed: {se}")

            # [New] Temp KB Search
            try:
                from app.services.rag.temp_kb import TempKnowledgeBase
                temp_kb = TempKnowledgeBase.get_instance()
                temp_refs = await temp_kb.search(session_id, message, top_k=5)
                if temp_refs:
                    references.extend(temp_refs)
                    # Re-sort and limit
                    references.sort(key=lambda x: x.get("score", 0), reverse=True)
                    references = references[:5]
                    
                    # Manually add temp refs to structured_refs
                    for tr in temp_refs:
                        structured_refs.append({
                            "id": 0,
                            "docId": 0,
                            "title": tr.get("title"),
                            "createTime": None,
                            "updateTime": None,
                            "coverImage": None,
                            "summary": tr.get("preview"),
                            "text": tr.get("content"),
                            "score": tr.get("score"),
                            "tags": ["temporary"],
                            "chunkId": tr.get("chunk_id"),
                            "pageNo": tr.get("page"),
                            "nodeId": tr.get("node_id")
                        })
            except Exception as e:
                logger.warning(f"Temp KB search failed: {e}")

            # 6. Stream Execution with CoT Parsing
            full_response = ""
            reasoning_content = ""
            has_started_reasoning = False
            has_ended_reasoning = False

            stream = []
            if target_agent_runner:
                try:
                    stream = target_agent_runner()
                    if inspect.isawaitable(stream):
                        stream = await stream
                except Exception as e:
                     if fallback_agent_runner:
                         stream = fallback_agent_runner()
                         if inspect.isawaitable(stream):
                             stream = await stream
                     else:
                         raise e
            else:
                 stream = self._run_deepseek_loop(agent, message, enable_search, agno_history)

            stream_gen = self._process_stream(stream)
            
            async for item in parse_thinking_stream(stream_gen):
                 if isinstance(item, dict) and item.get("type") == "think":
                      # Reasoning chunk
                      content = item.get("content", "")
                      reasoning_content += content
                      yield self._format_sse("think", content)
                 elif isinstance(item, dict) and item.get("type") in ["tool_start", "tool_end", "tool_error"]:
                      # Tool events
                      yield self._format_sse(item["type"], item)
                 elif isinstance(item, dict) and item.get("type") == "content":
                      # Content chunk
                      content = item.get("content", "")
                      full_response += content
                      yield self._format_sse("text", content)
                 elif isinstance(item, str):
                      # Fallback for raw string
                      full_response += item
                      yield self._format_sse("text", item)
            
            # Append References
            if references:
                formatted_refs = self._format_references(references)
                yield self._format_sse("text", formatted_refs)
                full_response += formatted_refs

            if structured_refs:
                yield self._format_sse("sources", structured_refs)

            # 7. Save Assistant Message
            meta = {
                "reasoning": reasoning_content,
                "references": references,
                "structured_references": structured_refs,
                "filtered_out": filtered_out if debug else [],
                "retrieval_note": retrieval_note,
                "strict_mode": strict_enabled,
                "ab_variant": ab_variant
            }
            meta = {k: v for k, v in meta.items() if v}
            
            await self._save_assistant_message(db, session_id, full_response, meta)
            yield self._format_sse("done", "[DONE]")

        except Exception as e:
            logger.error(f"Chat execution failed: {e}", exc_info=True)
            yield self._format_sse("error", f"Internal Server Error - {str(e)}")

    async def _load_agent(self, db, agent_id, session_id, enable_search):
        try:
            agent = await agent_manager.create_agno_agent(db, agent_id, session_id, enable_search=enable_search)
            res = await db.execute(select(Agent).filter(Agent.id == agent_id))
            agent_obj = res.scalars().first()
            return agent, agent_obj
        except Exception as e:
            logger.error(f"Failed to load agent {agent_id}: {e}")
            return None, None

    async def _create_default_agent(self, db, session_id, message, user_msg, enable_search, mode="chat"):
        # 1. Find active model
        res = await db.execute(
            select(LLMModel)
            .filter(LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
            .order_by(LLMModel.updated_at.desc())
        )
        active_model = res.scalars().first()
        
        deepseek_like = False
        agent = None
        agent_obj = None # No DB object for default agent

        if active_model:
             # Create temp agent
             default_tools = self._get_default_tools(mode)
             model_instance = ModelFactory.create_model(active_model)
             is_reasoning = ModelFactory.should_use_agno_reasoning(active_model)
             
             agent = AgnoAgent(
                name="Default Agent",
                model=model_instance,
                instructions="You are a helpful assistant.",
                markdown=True,
                reasoning=is_reasoning,
                tools=default_tools,
             )
             
             if default_tools:
                 agent.instructions += "\n" + self._get_kb_instructions()
                 if settings.OPENCLAW_BASE_URL and mode == "auto_task":
                      agent.instructions += "\n" + self._get_openclaw_instructions()
                 
             # Detect DeepSeek
             deepseek_like = self._detect_deepseek_model(active_model)
             
        elif agent_manager.has_global_api_key():
             # Fallback to OpenAI
             default_tools = self._get_default_tools(mode)
             agent = AgnoAgent(
                 name="Global Default Agent",
                 model=OpenAIChat(id="gpt-4o", api_key=settings.OPENAI_API_KEY),
                 instructions="You are a helpful assistant.",
                 markdown=True,
                 tools=default_tools
             )
             if default_tools:
                 agent.instructions += "\n" + self._get_kb_instructions()
                 if settings.OPENCLAW_BASE_URL and mode == "auto_task":
                      agent.instructions += "\n" + self._get_openclaw_instructions()
             
        return agent, agent_obj, deepseek_like

    def _get_default_tools(self, mode="chat"):
        tools = []
        try:
            from app.services.rag.retrieval.engines.lightrag import lightrag_engine
            if lightrag_engine.rag:
                from app.services.rag.mcp_server import search_knowledge_base, query_knowledge_graph
                tools.extend([search_knowledge_base, query_knowledge_graph])
        except Exception:
            pass
            
        # [Fix] Inject OpenClaw tools ONLY if mode is 'auto_task' and configured
        if settings.OPENCLAW_BASE_URL and mode == "auto_task":
            try:
                from app.services.openclaw import OpenClawTools
                tools.append(OpenClawTools())
                logger.info("[CHAT] Injected OpenClaw tools for Default Agent (Auto Task Mode)")
            except Exception as e:
                logger.error(f"[CHAT] Failed to inject OpenClaw tools: {e}")
                
        return tools

    def _get_kb_instructions(self):
        return """
## Knowledge Base Capabilities
You have access to an advanced Knowledge Graph retrieval system via tools:
1. `search_knowledge_base`: Use for finding specific documents or text chunks (Vector Search).
2. `query_knowledge_graph`: Use for complex questions requiring understanding of entity relationships, global themes, or multi-hop reasoning (Graph Search).
   - Use `mode='local'` for specific entities.
   - Use `mode='global'` for high-level summaries.
   - Use `mode='mix'` (default) for best hybrid results.
"""

    def _get_openclaw_instructions(self):
        return """
## OpenClaw Capabilities
You have FULL access to OpenClaw tools for automation tasks. You can and should use them directly:
1. `oc_web_search` / `oc_web_fetch`: Search and read web content.
2. `oc_browser`: Control a browser for screenshots, PDF generation, or UI interaction.
3. `oc_cron`: Create, list, and delete scheduled crawl tasks. USE THIS to create new tasks.
4. `oc_nodes`: Manage and execute commands on connected nodes.
5. `oc_message`: Send notifications.

When the user asks to "create a task", "crawl a site", or "configure automation", you MUST use these tools.
Do not say you cannot access the configuration; instead, use the tools to perform the actions.
"""

    def _detect_deepseek(self, agent, agent_obj):
        # ... logic from lines 108-134 of original chat.py ...
        if not agent: return False
        deepseek_like = False
        if agent_obj and hasattr(agent_obj, "model_config") and agent_obj.model_config:
             # Handle dict access for model_config if it's a dict (Pydantic model dump or JSON field)
             conf = agent_obj.model_config
             mid = ""
             if isinstance(conf, dict):
                 mid = (conf.get("model_id") or "").lower()
             elif hasattr(conf, "model_id"):
                 mid = (conf.model_id or "").lower()
                 
             if "deepseek" in mid or "reasoner" in mid or "r1" in mid:
                return True
        
        model_obj = getattr(agent, "model", None)
        if model_obj:
            mid = (getattr(model_obj, "id", "") or "").lower()
            base = (getattr(model_obj, "base_url", "") or "").lower()
            provider = (getattr(model_obj, "provider", "") or "").lower()
            deepseek_like = ("deepseek" in base) or ("deepseek" in mid) or ("reasoner" in mid) or ("r1" in mid) or ("deepseek" in provider) or ("aliyun" in provider) or ("siliconflow" in provider)
            
        return deepseek_like

    def _detect_deepseek_model(self, model: LLMModel):
        mid = (model.model_id or "").lower()
        base = (model.base_url or "").lower()
        provider = (model.provider or "").lower()
        return ("deepseek" in mid) or ("reasoner" in mid) or ("r1" in mid) or ("deepseek" in base) or ("deepseek" in provider) or ("aliyun" in provider) or ("siliconflow" in provider)

    async def _build_history(self, db, session_id, user_msg, deepseek_like):
        history_msgs = await crud_chat.get_history(db, session_id)
        agno_history = []
        for msg in history_msgs:
            if msg.id == user_msg.id: continue
            msg_dict = {"role": msg.role, "content": msg.content}
            if msg.role == "assistant":
                reasoning = ""
                if msg.meta_data and "reasoning" in msg.meta_data:
                    reasoning = msg.meta_data["reasoning"]
                
                if reasoning:
                    msg_dict["reasoning_content"] = reasoning
                elif deepseek_like:
                    msg_dict["reasoning_content"] = ""
            agno_history.append(msg_dict)
            
        # Use ContextCompressor for intelligent context management
        try:
            from app.core.context_compressor import ContextCompressor
            compressor = ContextCompressor()
            return await compressor.compress_context(agno_history)
        except Exception as e:
            logger.error(f"Context compression failed: {e}. Falling back to simple truncation.")
            from app.core.context_utils import get_optimized_context
            return get_optimized_context(agno_history)

    async def _get_allowed_docs(self, db, agent_obj, attachments, strict_mode):
        doc_ids = []
        if agent_obj and agent_obj.knowledge_config:
            doc_ids = list(agent_obj.knowledge_config.get("document_ids") or [])
        if attachments:
            doc_ids.extend(attachments)
        doc_ids = list(set(doc_ids))
        
        allowed_names = []
        if doc_ids:
            res = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id.in_(doc_ids)))
            docs = res.scalars().all()
            allowed_names = [d.filename for d in docs if d.filename]
            
        strict_enabled = bool(
            strict_mode or 
            (agent_obj and agent_obj.knowledge_config and agent_obj.knowledge_config.get("strict_only"))
        )
        return allowed_names, strict_enabled

    async def _build_structured_refs(self, db, references):
        if not references: return []
        titles = [r.get("title") for r in references if r.get("title")]
        if not titles: return []
        
        res = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.filename.in_(titles)))
        docs = res.scalars().all()
        idx = {d.filename: d for d in docs}
        
        structured = []
        for r in references:
            t = r.get("title")
            d = idx.get(t)
            structured.append({
                "id": d.id if d else 0,
                "docId": d.id if d else 0,
                "title": t,
                "createTime": d.created_at.isoformat() if d else None,
                "updateTime": d.updated_at.isoformat() if d else None,
                "coverImage": d.oss_url if d else r.get("url"),
                "summary": r.get("preview") or "",
                "text": r.get("content") or r.get("preview"),
                "score": r.get("score") or 0,
                "tags": [],
                "chunkId": r.get("chunk_id"),
                "pageNo": r.get("page"),
                "nodeId": r.get("node_id")
            })
        return structured

    async def _run_deepseek_loop(self, agent, message, enable_search, history):
        model_obj = getattr(agent, "model", None)
        api_key = getattr(model_obj, "api_key", None) or ""
        base_url = getattr(model_obj, "base_url", None)
        model_id = getattr(model_obj, "id", None) or "deepseek-reasoner"
        
        client = OpenAI(api_key=api_key or "dummy", base_url=base_url)
        ddg = DuckDuckGoTools()
        tools = []
        
        if enable_search:
            tools.append({
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
            })

        tools.append({
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
            })

        def _get_datetime(format: str = None):
            from datetime import datetime
            if format:
                try:
                    return {"now": datetime.now().strftime(format)}
                except:
                    pass
            return {"now": datetime.now().isoformat()}

        tool_map = {
            "get_datetime": lambda format=None: _get_datetime(format),
        }
        
        if enable_search:
            tool_map["duckduckgo_search"] = lambda query, max_results=5: (
                json.loads(ddg.search(query, max_results=max_results))
                if ddg
                else {"error": "ddg not available"}
            )

        # Inject Knowledge Base Tool if agent has KB configured
        # [Fix] Also check if agent has tools injected (MCP tools)
        kb = getattr(agent, "knowledge", None)
        
        # If knowledge object is missing (new architecture), check tools list
        has_kb_tools = False
        if not kb and agent.tools:
             for t in agent.tools:
                 if hasattr(t, "__name__") and ("search_knowledge_base" in t.__name__ or "query_knowledge_graph" in t.__name__):
                     has_kb_tools = True
                     break
        
        if kb or has_kb_tools:
            # Add search_knowledge_base schema
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": "search_knowledge_base",
                        "description": "Search the knowledge base for relevant documents.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search query"},
                                "num_documents": {"type": "integer", "description": "Number of documents to return", "default": 5}
                            },
                            "required": ["query"],
                        },
                    },
                }
            )
            
            # Add query_knowledge_graph schema
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": "query_knowledge_graph",
                        "description": "Perform an advanced graph-based search on the knowledge base.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The question to ask"},
                                "mode": {"type": "string", "enum": ["mix", "local", "global"], "default": "mix"}
                            },
                            "required": ["query"],
                        },
                    },
                }
            )
            
            # Define implementation wrappers
            # We need to import the actual functions from mcp_server if they are not available via `kb` object
            from app.services.rag.mcp_server import search_knowledge_base, query_knowledge_graph
            
            async def _search_kb_wrapper(query: str, num_documents: int = 5):
                 return await search_knowledge_base(query, num_documents)
            
            async def _query_graph_wrapper(query: str, mode: str = "mix"):
                return await query_knowledge_graph(query, mode)

            tool_map["search_knowledge_base"] = _search_kb_wrapper
            tool_map["query_knowledge_graph"] = _query_graph_wrapper

        # Only enable thinking for DeepSeek Reasoner models
        is_deepseek = "deepseek" in model_id.lower() and (
            "reasoner" in model_id.lower() or "r1" in model_id.lower()
        )

        res = await run_reasoning_tool_loop(
            client=client,
            model_id=model_id,
            user_prompt=message,
            tools=tools,
            tool_call_map=tool_map,
            enable_thinking=is_deepseek,
            messages=history,  # Pass history
        )
        final_msg = res["final_message"]
        rc = getattr(final_msg, "reasoning_content", None) or None
        if rc:
            yield "<think>\n"
            yield rc
            yield "\n</think>\n"
        content_text = getattr(final_msg, "content", "") or ""
        yield content_text

    async def _process_stream(self, stream):
        if inspect.isasyncgen(stream):
            async for item in stream:
                if isinstance(item, str):
                    yield item
                elif hasattr(item, "content"):
                    # Handle RunOutputEvent from Agno
                    event_type = getattr(item, "event", None)
                    
                    # 1. Text Content
                    if event_type in ["RunContent", "RunIntermediateContent", "RunContentCompleted", "ReasoningContentDelta"]:
                         if hasattr(item, "content") and item.content:
                             yield str(item.content)
                         elif hasattr(item, "reasoning_content") and item.reasoning_content:
                             # Map Agno reasoning to <think> format if not already
                             yield f"<think>{item.reasoning_content}</think>"
                    
                    # 2. Tool Call Started
                    elif event_type == "ToolCallStarted":
                        tool = getattr(item, "tool", None)
                        if tool:
                            tool_dict = tool.to_dict() if hasattr(tool, "to_dict") else str(tool)
                            yield {"type": "tool_start", "tool": tool_dict}
                    
                    # 3. Tool Call Completed
                    elif event_type == "ToolCallCompleted":
                        tool = getattr(item, "tool", None)
                        content = getattr(item, "content", None)
                        if tool:
                            tool_dict = tool.to_dict() if hasattr(tool, "to_dict") else str(tool)
                            yield {"type": "tool_end", "tool": tool_dict, "result": str(content)}
                            
                    # 4. Tool Call Error
                    elif event_type == "ToolCallError":
                        tool = getattr(item, "tool", None)
                        error = getattr(item, "error", None)
                        if tool:
                            tool_dict = tool.to_dict() if hasattr(tool, "to_dict") else str(tool)
                            yield {"type": "tool_error", "tool": tool_dict, "error": str(error)}
                    
                    # Fallback for legacy objects or simple RunResponse
                    elif not event_type: 
                        yield str(item.content) if item.content is not None else ""
                else:
                    yield str(item)
        else:
            for item in stream:
                if isinstance(item, str):
                    yield item
                elif hasattr(item, "content"):
                    yield str(item.content) if item.content is not None else ""
                else:
                    yield str(item)

    def _format_references(self, references):
        citations = ["\n\nReferences:"]
        for i, r in enumerate(references, 1):
            title = r.get("title") or ""
            url = r.get("url") or ""
            page = r.get("page")
            score = r.get("score")
            preview = r.get("preview") or ""
            line = f"{i}. {title}"
            if page is not None: line += f" (page {page})"
            if url: line += f" - {url}"
            if score is not None: line += f" [score {score:.2f}]"
            citations.append(line)
            if preview: citations.append(f"   Preview: {preview}")
        return "\n".join(citations) + "\n"

    async def _save_assistant_message(self, db, session_id, content, meta):
        try:
            msg = await crud_chat.create_message(
                db, session_id, "assistant", content, {"reasoning": meta.get("reasoning")} if meta.get("reasoning") else None
            )
            await crud_chat.update_message_meta(db, session_id, meta, message_id=msg.id)
        except Exception as e:
            logger.error(f"Failed to save assistant message: {e}")

chat_service = ChatService()
