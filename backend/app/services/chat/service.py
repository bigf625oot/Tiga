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
from app.services.agent.manager import agent_manager
from app.services.llm.factory import ModelFactory
from app.services.rag.knowledge_base import kb_service
from app.core.config import settings
from agno.agent import Agent as AgnoAgent
from agno.models.openai import OpenAIChat
from openai import OpenAI
from app.services.agent.tools.duckduckgo import DuckDuckGoTools
from app.services.agent.tools.runner import run_reasoning_tool_loop
from datetime import datetime

class ChatService:
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
        
        # 1. Get Session
        logger.info(f"[CHAT] Starting chat for session={session_id}")
        session = await crud_chat.get(db, session_id)
        if not session:
            logger.error(f"[CHAT] Session {session_id} not found")
            yield "Error: Session not found"
            return

        # 2. Save User Message
        logger.debug(f"[CHAT] User message: {message[:50]}...")
        user_msg = await crud_chat.create_message(db, session_id, "user", message)

        # 3. Initialize Agent
        agent = None
        agent_obj = None
        target_agent_runner = None
        fallback_agent_runner = None
        deepseek_like = False

        if session.agent_id:
            agent, agent_obj = await self._load_agent(db, session.agent_id, session_id, enable_search)
            if not agent:
                 yield "Error: Failed to load agent."
                 return
        else:
            agent, agent_obj, target_agent_runner, fallback_agent_runner, deepseek_like = await self._create_default_agent(db, session_id, message, user_msg, enable_search)
            if not agent:
                 yield "Error: Failed to initialize default agent."
                 return

        # 4. DeepSeek Logic for Custom Agent
        if session.agent_id and agent:
            deepseek_like = self._detect_deepseek(agent, agent_obj)
            agno_history = await self._build_history(db, session_id, user_msg, deepseek_like)
            
            if deepseek_like:
                target_agent_runner = None
                logger.info("[CHAT] Using specialized DeepSeek/Tool runner path")
            else:
                async def _standard_runner():
                    return await agent.arun(message, stream=True, messages=agno_history)
                
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

        # 6. Stream Execution
        full_response = ""
        reasoning_content = ""
        has_started_reasoning = False
        has_ended_reasoning = False

        try:
            stream = []
            if target_agent_runner:
                try:
                    stream = target_agent_runner()
                    if inspect.isawaitable(stream):
                        stream = await stream
                except Exception as e:
                     # Fallback logic
                     if fallback_agent_runner:
                         stream = fallback_agent_runner()
                         if inspect.isawaitable(stream):
                             stream = await stream
                     else:
                         raise e
            else:
                 # DeepSeek Tool Loop
                 stream = self._run_deepseek_loop(agent, message, enable_search, agno_history)

            async for item in self._process_stream(stream):
                 # Handle reasoning tags
                 if item.startswith("<think>") or item.startswith("\n</think>"):
                      if item.startswith("<think>"):
                           has_started_reasoning = True
                           yield item
                      else:
                           has_ended_reasoning = True
                           yield item
                 elif has_started_reasoning and not has_ended_reasoning:
                      reasoning_content += item
                      yield item
                 else:
                      full_response += item
                      yield item
            
            # Close reasoning if needed
            if has_started_reasoning and not has_ended_reasoning:
                yield "\n</think>\n"

            # Append References
            if references:
                yield self._format_references(references)

            if structured_refs:
                yield f"\n\n__SOURCES__\n{json.dumps(structured_refs, ensure_ascii=False)}\n"

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
            # Clean empty keys
            meta = {k: v for k, v in meta.items() if v}
            
            await self._save_assistant_message(db, session_id, full_response, meta)

        except Exception as e:
            logger.error(f"Chat execution failed: {e}", exc_info=True)
            yield f"Error: {str(e)}"

    async def _load_agent(self, db, agent_id, session_id, enable_search):
        try:
            agent = await agent_manager.create_agno_agent(db, agent_id, session_id, enable_search=enable_search)
            res = await db.execute(select(Agent).filter(Agent.id == agent_id))
            agent_obj = res.scalars().first()
            return agent, agent_obj
        except Exception as e:
            logger.error(f"Failed to load agent {agent_id}: {e}")
            return None, None

    async def _create_default_agent(self, db, session_id, message, user_msg, enable_search):
        # ... Implementation of default agent creation (extracted from original chat.py) ...
        # For brevity, I will simplify this in the first pass or copy the logic.
        # Let's copy the logic to ensure fidelity.
        
        # 1. Find active model
        res = await db.execute(
            select(LLMModel)
            .filter(LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
            .order_by(LLMModel.updated_at.desc())
        )
        active_model = res.scalars().first()
        
        target_agent_runner = None
        fallback_agent_runner = None
        deepseek_like = False
        agent = None
        agent_obj = None # No DB object for default agent

        if active_model:
             # Create temp agent
             default_tools = self._get_default_tools()
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
                 
             # Detect DeepSeek
             deepseek_like = self._detect_deepseek_model(active_model)
             
             # History
             agno_history = await self._build_history(db, session_id, user_msg, deepseek_like)
             
             async def _runner():
                 return await agent.arun(message, stream=True, messages=agno_history)
             
             async def _fallback():
                 res = await agent.arun(message, stream=False, messages=agno_history)
                 return [res]
                 
             target_agent_runner = _runner
             fallback_agent_runner = _fallback
             
        elif agent_manager.has_global_api_key():
             # Fallback to OpenAI
             default_tools = self._get_default_tools()
             agent = AgnoAgent(
                 name="Global Default Agent",
                 model=OpenAIChat(id="gpt-4o", api_key=settings.OPENAI_API_KEY),
                 instructions="You are a helpful assistant.",
                 markdown=True,
                 tools=default_tools
             )
             if default_tools:
                 agent.instructions += "\n" + self._get_kb_instructions()
                 
             agno_history = await self._build_history(db, session_id, user_msg, False)
             
             async def _runner():
                 return await agent.arun(message, stream=True, messages=agno_history)
             async def _fallback():
                 res = await agent.arun(message, stream=False, messages=agno_history)
                 return [res]
                 
             target_agent_runner = _runner
             fallback_agent_runner = _fallback
             
        return agent, agent_obj, target_agent_runner, fallback_agent_runner, deepseek_like

    def _get_default_tools(self):
        tools = []
        try:
            from app.services.rag.engines.lightrag import lightrag_engine
            if lightrag_engine.rag:
                from app.services.rag.mcp_server import search_knowledge_base, query_knowledge_graph
                tools.extend([search_knowledge_base, query_knowledge_graph])
        except Exception:
            pass
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
        return agno_history

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
                yield item
        else:
            for item in stream:
                yield item

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
