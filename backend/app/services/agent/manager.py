import logging
import inspect

from agno.agent import Agent as AgnoAgent
from agno.tools.duckduckgo import DuckDuckGoTools
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# from agno.tools.python import PythonTools # Assuming this exists or similar
from app.models.agent import Agent as AgentModel
from app.models.chat import ChatMessage
from app.models.llm_model import LLMModel
from app.services.rag.knowledge_base import kb_service
from app.services.agent.skills import Skills as FileSkillsManager, LocalSkills

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.llm.factory import ModelFactory
from app.services.tools.discovery import discover_tools

try:
    from app.services.mcp_client import mcp_pool
except Exception:
    mcp_pool = None


def has_global_api_key():
    return bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"))


class AgentManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_agno_agent(self, db: AsyncSession, agent_id: str, session_id: str = None, enable_search: bool = True) -> AgnoAgent:
        try:
            # 1. Fetch Agent Config
            result = await db.execute(select(AgentModel).filter(AgentModel.id == agent_id))
            agent_model = result.scalars().first()
            if not agent_model:
                raise ValueError(f"Agent {agent_id} not found")

            # 2. Fetch Model Config
            # Schema field is 'agent_model_config' but DB model uses 'model_config' (JSON)
            # SQLAlchemy model (AgentModel) uses 'model_config'.
            # Pydantic schema (AgentCreate/Response) uses 'agent_model_config'.
            # Here we are reading from DB model (SQLAlchemy), so it is 'model_config'.
            model_config = getattr(agent_model, "model_config", {}) or {}
            llm_model_id = model_config.get("model_id")

            llm_model = None
            if llm_model_id:
                # Find the active model config from DB
                # First try to find active model with this model_id AND a non-empty API key
                res = await db.execute(
                    select(LLMModel).filter(
                        LLMModel.model_id == llm_model_id,
                        LLMModel.is_active == True,
                        LLMModel.api_key != None,
                        LLMModel.api_key != "",
                    )
                )
                llm_model = res.scalars().first()

                # If not found, fall back to just matching model_id (maybe user relies on env var, though unlikely for custom)
                if not llm_model:
                    res = await db.execute(
                        select(LLMModel).filter(LLMModel.model_id == llm_model_id, LLMModel.is_active == True)
                    )
                    llm_model = res.scalars().first()

            # Fallback to default if not found or if found model has no key and global key is missing
            # We check if the found model has a valid key. If not, and we are here, it means we might crash.
            # So we try to find ANY model with a valid key.

            should_fallback = False
            if not llm_model:
                should_fallback = True
            # IMPORTANT: Check if llm_model has api_key. If not, check global key.
            # If both are missing, we MUST fallback.
            elif not llm_model.api_key and not has_global_api_key():
                should_fallback = True

            if should_fallback:
                # Try to find ANY active model with a valid key
                res = await db.execute(
                    select(LLMModel)
                    .filter(LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
                    .order_by(LLMModel.updated_at.desc())
                )
                fallback_model = res.scalars().first()
                if fallback_model:
                    if llm_model:
                        logger.warning(
                            f"Agent requested model {llm_model.model_id} which has no key. Falling back to {fallback_model.model_id}."
                        )
                    llm_model = fallback_model
                else:
                    # If still no model, maybe use the one without key and hope for the best (will likely fail with dummy)
                    if not llm_model:
                        # Re-fetch any active model even without key
                        res = await db.execute(
                            select(LLMModel).filter(LLMModel.is_active == True).order_by(LLMModel.updated_at.desc())
                        )
                        llm_model = res.scalars().first()

            if not llm_model:
                raise ValueError("No active LLM model found")

            # 3. Configure LLM using Factory
            model = ModelFactory.create_model(llm_model)

            # 4. Configure Tools
            tools = []
            # IMPORTANT: We use 'getattr' to safely access Pydantic model fields or dict keys if mixed types.
            # In production, these are SQLAlchemy models, so attribute access is correct.
            # But tests use Mocks which might fail if attribute is missing.
            tools_config = getattr(agent_model, "tools_config", []) or []
            skills_config = getattr(agent_model, "skills_config", {}) or {}
            mcp_config = getattr(agent_model, "mcp_config", []) or []

            # --- Dynamic Python Tools Integration ---
            # Discover available tools from backend/app/services/tools
            available_tools = discover_tools()
            loaded_dynamic_tools = set()

            if isinstance(tools_config, list):
                for tool_entry in tools_config:
                    if isinstance(tool_entry, str):
                        tool_name = tool_entry.lower()
                        if tool_name in available_tools:
                            try:
                                ToolClass = available_tools[tool_name]
                                # Instantiate tool with default config
                                tools.append(ToolClass())
                                loaded_dynamic_tools.add(tool_name)
                                logger.info(f"Loaded dynamic tool: {tool_name}")
                            except Exception as e:
                                logger.error(f"Failed to load dynamic tool {tool_name}: {e}")

            # Instructions handling (Base)
            instructions = getattr(agent_model, "system_prompt", None) or "You are a helpful assistant."
            
            # --- Market Skills Integration ---
            # Extract skills from tools_config (mixed list of strings and objects)
            market_skills = [t for t in tools_config if isinstance(t, dict) and t.get('type') == 'skill']
            if market_skills:
                skill_instructions = []
                for skill in market_skills:
                    if skill.get('content'):
                        skill_instructions.append(f"### Skill: {skill.get('name')}\n{skill.get('content')}")
                
                if skill_instructions:
                    instructions += "\n\n## Enabled Skills\n" + "\n\n".join(skill_instructions)
            
            # --- File Skills Integration (New) ---
            # Enable file-based skills if configured
            # Check skills_config first, then fallback to checking if directory exists and is implicitly enabled
            file_skills_config = skills_config.get("file_skills", {})
            is_file_skills_enabled = file_skills_config.get("enabled", False)
            
            if is_file_skills_enabled:
                try:
                    from pathlib import Path
                    # Default path or configured path
                    # Handle relative paths from project root
                    skills_path_str = file_skills_config.get("path", "app/data/skills")
                    skills_dir = Path(skills_path_str)
                    
                    if not skills_dir.is_absolute():
                         # Assuming we are in backend root
                         skills_dir = Path.cwd() / skills_dir
                    
                    if skills_dir.exists():
                        # IMPORTANT: Use the local loader from the package we fixed
                        # Using 'loader' variable name that doesn't conflict
                        fs_loader = LocalSkills(path=str(skills_dir))
                        skills_mgr = FileSkillsManager(loaders=[fs_loader])
                        
                        # Inject management tools
                        skill_tools = skills_mgr.get_tools()
                        if skill_tools:
                            tools.extend(skill_tools)
                            logger.info(f"Injected {len(skill_tools)} File Skills tools for agent {agent_model.name} from {skills_dir}")
                            
                            # Add system prompt snippet
                            # Append to instructions so the model knows about them
                            sys_prompt_snippet = skills_mgr.get_system_prompt_snippet()
                            if sys_prompt_snippet:
                                instructions += "\n\n" + sys_prompt_snippet
                    else:
                        logger.warning(f"File skills directory not found: {skills_dir}")
                except Exception as e:
                    logger.error(f"Failed to load file skills: {e}")

            # --- MCP Integration ---
            if mcp_config:
                try:
                    from app.services.agent.tools.factory import get_mcp_toolkit

                    for mcp_server in mcp_config:
                        # Normalize config
                        # If 'url' is missing but 'command' is present, it's a stdio config
                        # If 'url' is present, check protocol
                        
                        try:
                            # Use factory to get appropriate toolkit
                            # Pass the entire config dict, factory handles logic
                            toolkit = await get_mcp_toolkit(mcp_server, agent_id=agent_model.id)
                            tools.append(toolkit)
                            logger.info(f"Successfully loaded MCP toolkit for {mcp_server.get('url') or mcp_server.get('command')}")
                            
                        except Exception as e:
                            logger.error(f"Failed to initialize MCP client for {mcp_server}: {e}")
                except ImportError as e:
                    logger.error(f"MCP Client services not available: {e}")
                except Exception as e:
                    logger.error(f"Error loading MCP tools: {e}")

            # OpenClaw Tools (Auto-inject if configured)
            from app.core.config import settings
            # Inject OpenClaw tools if base_url is present (default is set)
            # Token is optional for local dev or unsecured gateway
            if settings.OPENCLAW_BASE_URL:
                try:
                    from app.services.openclaw import OpenClawTools
                    # Inject OpenClaw tools
                    tools.append(OpenClawTools())
                    logger.info(f"Injected OpenClaw tools for agent {agent_model.name}")
                    
                    oc_instructions = """
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
                    if "OpenClaw Capabilities" not in instructions:
                        instructions += "\n" + oc_instructions
                except Exception as e:
                    logger.error(f"Failed to inject OpenClaw tools: {e}")

            # Standard Tools
            # Check if "duckduckgo" is in tools_config AND NOT loaded dynamically (to avoid duplicates)
            # Or if browser skill is enabled
            use_duckduckgo = ("duckduckgo" in tools_config and "duckduckgo" not in loaded_dynamic_tools) or (skills_config.get("browser", {}).get("enabled"))
            
            if use_duckduckgo and enable_search:
                tools.append(DuckDuckGoTools())

            # N8N Tools
            if "n8n" in tools_config:
                try:
                    from app.tools.n8n import N8NTools

                    from app.models.workflow import Workflow

                    # Fetch active workflows
                    wf_res = await db.execute(select(Workflow).filter(Workflow.is_active == True))
                    workflows = wf_res.scalars().all()
                    if workflows:
                        # Convert to dicts
                        wf_dicts = [{"name": w.name, "webhook_url": w.webhook_url} for w in workflows]
                        tools.append(N8NTools(workflows=wf_dicts))
                except ImportError:
                    logger.warning("N8NTools module not found, skipping n8n tools.")

            # Python Tools (Mock or Real)
            if skills_config.get("python", {}).get("enabled"):
                # from agno.tools.python import PythonTools
                # tools.append(PythonTools())
                pass  # Skipping for now as environment might lack dependencies

            # E2B Sandbox Tools
            # Enable if 'sandbox' skill is enabled OR if 'sb_shell_tool' (legacy name) is in tools_config
            is_sandbox_enabled = skills_config.get("sandbox", {}).get("enabled")
            
            # Also check legacy tool names in tools_config list
            if not is_sandbox_enabled and isinstance(tools_config, list):
                for t in tools_config:
                    if isinstance(t, str) and t.startswith("sb_"):
                        is_sandbox_enabled = True
                        break
            
            if is_sandbox_enabled:
                try:
                    from app.services.agent.tools.sandbox_tools import SandboxTools
                    # Use session_id if available to persist context
                    # If session_id is None, SandboxTools might create a new session or use ephemeral
                    tools.append(SandboxTools(session_id=session_id))
                    logger.info(f"Injected Sandbox tools for agent {agent_model.name}")
                    
                    # Append instructions
                    sb_instructions = """
## Sandbox Capabilities
You have access to a secure E2B sandbox environment. You can:
1. Execute Python code using `run_code`.
2. Run shell commands using `run_shell` (e.g., install packages, run other languages).
3. Manage files using `read_file`, `write_file`, `list_files`.

When asked to write code or perform tasks:
- Always check the environment first if unsure (e.g., `list_files`).
- Write necessary files before executing them.
- If you need to install packages, use `run_shell('pip install package')`.
"""
                    if "Sandbox Capabilities" not in instructions:
                        instructions += "\n" + sb_instructions
                except Exception as e:
                    logger.error(f"Failed to inject Sandbox tools: {e}")

            # Knowledge Base
            # [Refactor] Using MCP Tools instead of Agno Knowledge Adapter
            # This avoids 'vector_db' validation issues and standardizes tool usage.
            
            # Check if kb_service is initialized properly
            # IMPORTANT: We use 'getattr' again to be safe with Mocks in tests
            is_knowledge_configured = getattr(agent_model, "knowledge_config", None) is not None
            has_documents = False
            
            knowledge_config = getattr(agent_model, "knowledge_config", None)
            if knowledge_config and isinstance(knowledge_config, dict):
                has_documents = bool(knowledge_config.get("document_ids"))
            
            if is_knowledge_configured or has_documents:
                # Add Knowledge Base Tools directly
                try:
                    from app.services.rag.mcp_server import search_knowledge_base, query_knowledge_graph
                    tools.extend([search_knowledge_base, query_knowledge_graph])
                    logger.info(f"Injected LightRAG MCP tools for agent {agent_model.name}")
                    
                    # [Feature] Auto-append System Prompt for Knowledge Graph capabilities
                    # Since we are using advanced graph retrieval, we should guide the model on when to use it.
                    kb_instructions = """
## Knowledge Base Capabilities
You have access to an advanced Knowledge Graph retrieval system via tools:
1. `search_knowledge_base`: Use for finding specific documents or text chunks (Vector Search).
2. `query_knowledge_graph`: Use for complex questions requiring understanding of entity relationships, global themes, or multi-hop reasoning (Graph Search).
   - Use `mode='local'` for specific entities.
   - Use `mode='global'` for high-level summaries.
   - Use `mode='mix'` (default) for best hybrid results.
"""
                    if "Knowledge Base Capabilities" not in instructions:
                        instructions += "\n" + kb_instructions

                except ImportError as e:
                    logger.error(f"Failed to import LightRAG MCP tools: {e}")

            # NOTE: We no longer set 'knowledge' or 'search_knowledge' on the AgnoAgent.
            # The capability is now provided via standard tools.
            search_knowledge = False 
            knowledge = None

            # 5. Load History
            history = []
            if session_id:
                # Load recent messages (e.g. last 20)
                msgs = await db.execute(
                    select(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc())
                )
                chat_logs = msgs.scalars().all()
                pass

            # 6. Create Agent
            is_reasoning = ModelFactory.should_use_agno_reasoning(llm_model)
            # is_native_reasoning = ModelFactory.is_reasoning_model(llm_model) # Unused

            # Instructions are prepared above (including Skills)

            agent = AgnoAgent(
                name=agent_model.name,
                model=model,
                description=getattr(agent_model, "description", None),  # Pass description
                instructions=instructions,
                tools=tools,
                # knowledge=knowledge, # Deprecated
                # search_knowledge=search_knowledge, # Deprecated
                markdown=True,
                reasoning=is_reasoning,
                # show_reasoning=True, # Removed as it causes TypeError in current Agno version
                debug_mode=True, # Enable debug logs to trace tool calls
            )

            # [Patch] Inject knowledge object directly into agent instance
            # AgnoAgent might not expose 'knowledge' as a public attribute in some versions,
            # or we need to access it later in agent_execute_step.
            # if knowledge:
            #    agent.knowledge = knowledge

            return agent
        except Exception as e:
            logger.exception(f"Error creating agent {agent_id}")
            raise e

    async def get_planner_agent(self, db: AsyncSession, model_id: str = "gpt-4-turbo") -> 'PlannerAgent':
        from app.services.agent.planner import PlannerAgent
        return PlannerAgent(self, db, model_id)

    async def get_executor_agent(self, db: AsyncSession, agent_id: str = None) -> 'ExecutorAgent':
        from app.services.agent.executor import ExecutorAgent
        return ExecutorAgent(self, db)

agent_manager = AgentManager.get_instance()
