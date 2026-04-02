"""
智能体构建器
场景：
- 当用户创建一个新的智能体时，需要根据用户输入的配置信息，构建一个符合要求的智能体。
- 当用户更新一个智能体的配置信息时，需要根据新的配置信息，重新构建智能体。
"""
import asyncio
import logging
from typing import Optional, List, Any, Dict, Protocol, runtime_checkable
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from agno.agent import Agent as AgnoAgent

# 内部模块依赖 (假设已按 Clean Architecture 划分)
from app.core.exceptions import AgentBuildError, ModelNotFoundError
from app.models.agent import Agent as AgentModel
from app.models.llm_model import LLMModel
from app.services.agent.schemas.prompt import InstructionComposer, InstructionSegment, InstructionCategory
from app.services.agent.tools import default_tools
from app.services.agent.tools.tool_factory import ToolFactory
from app.services.agent.skills.loaders.local import LocalSkills
from app.services.agent.skills.manager import Skills
from app.services.agent.utils.secret_refs import resolve_secret_refs
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- 1. 契约定义 (Protocols) ---
# P10 级代码强调“面向接口编程”，确保系统高度解耦

@runtime_checkable
class ToolWithPrompt(Protocol):
    """定义工具提取提示词的标准协议"""
    def get_system_prompt_snippet(self) -> Optional[str]: ...

@dataclass
class BuildContext:
    """构建上下文：存储构建过程中的中间状态，避免长参数传递"""
    agent_id: str
    session_id: Optional[str] = None
    agent_model: Optional[AgentModel] = None
    llm_model: Optional[LLMModel] = None
    tools: List[Any] = field(default_factory=list)
    instruction_builder: Optional[InstructionComposer] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- 2. 核心构建策略 (Strategies) ---

class ModelSelector:
    """模型选择策略：处理复杂的降级逻辑"""
    
    @staticmethod
    async def select(db: AsyncSession, target_id: Optional[str]) -> LLMModel:
        stmt = select(LLMModel).where(LLMModel.is_active).order_by(LLMModel.updated_at.desc())
        result = await db.execute(stmt)
        active_models = result.scalars().all()
        
        if not active_models:
            raise ModelNotFoundError("No active LLM models configured in system.")

        def is_viable(m: LLMModel) -> bool:
            has_key = bool(m.api_key and m.api_key.strip())
            has_global = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"))
            return has_key or has_global

        target = next((m for m in active_models if m.model_id == target_id), None)
        if target and is_viable(target):
            return target
        
        fallback = next((m for m in active_models if m.api_key and m.api_key.strip()), active_models[0])
        logger.warning(f"Model fallback triggered: {target_id} -> {fallback.model_id}")
        return fallback

# --- 3. 主构建流水线 (The Assembler) ---

class AgentAssembler:
    """
    P10 级 Agent 构建器：基于 Pipeline 模式
    职责：解耦配置加载、工具装配、指令合成与实例实例化。
    """
    
    _skills_manager: Optional[Skills] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_skills_manager(cls) -> Optional[Skills]:
        """单例模式加载技能管理器"""
        if cls._skills_manager is None:
            async with cls._lock:
                if cls._skills_manager is None:
                    from pathlib import Path
                    path = Path(__file__).parent.parent / "skills"
                    if path.exists():
                        loader = LocalSkills(str(path), validate=False)
                        cls._skills_manager = Skills([loader])
                    else:
                        logger.warning(f"Skills path missing: {path}")
        return cls._skills_manager

    def __init__(self, db: AsyncSession, agent_id: str):
        self.db = db
        self.ctx = BuildContext(agent_id=agent_id)

    async def build(self, **overrides) -> AgnoAgent:
        """核心构建流"""
        try:
            if not self.ctx.agent_model:
                await self._load_essential_data()
            
            intent = overrides.get("intent")
            suggested_tools = intent.suggested_tools if intent else []

            await self._assemble_toolset(
                session_id=overrides.get("session_id"),
                enable_search=overrides.get("enable_search"),
                suggested_tools=suggested_tools
            )
            
            # Inject intent-based tools directly into ctx.tools to avoid modifying DB model
            if intent:
                intent_key = intent.intent.value if hasattr(intent.intent, "value") else str(intent.intent)
                if intent_key in ("data_query", "kg_qa"):
                    # check if data_toolkit is already loaded
                    has_data_tool = any(getattr(t, "name", "") == "data_toolkit" for t in self.ctx.tools)
                    if not has_data_tool:
                        from app.services.agent.tools.libs.data_toolkit import DataToolkit
                        dt = DataToolkit()
                        self.ctx.tools.append(dt)
                        snippet = dt.get_system_prompt_snippet()
                        if snippet:
                            self.ctx.instruction_builder.with_file_skill(snippet)
            
            final_instructions = self._orchestrate_instructions()
            
            agent_kwargs = self._prepare_agno_params(final_instructions, overrides)
            
            return await self._finalize_instance(agent_kwargs)
            
        except Exception as e:
            logger.error(f"Failed to build agent {self.ctx.agent_id}: {str(e)}", exc_info=True)
            raise AgentBuildError(f"Critical failure in AgentAssembler: {e}")

    async def _load_essential_data(self):
        """加载 Agent 和 Model 数据"""
        if self.ctx.agent_id:
            res = await self.db.execute(select(AgentModel).filter(AgentModel.id == self.ctx.agent_id))
            self.ctx.agent_model = res.scalars().first()
            if not self.ctx.agent_model:
                raise AgentBuildError(f"Agent entity {self.ctx.agent_id} missing")
        else:
            self.ctx.agent_model = AgentModel(
                id="default_adhoc_agent",
                name="Assistant",
                description="Default Chat Assistant",
                system_prompt="You are a helpful assistant.",
                instructions=[],
                model_config={"enable_search": True},
                tools_config=[],
                skills_config={"file_skills": {"enabled": True, "path": "c:/Users/fenda/.trae/skills"}},
                knowledge_config={}
            )

        self.ctx.llm_model = await ModelSelector.select(
            self.db, 
            self.ctx.agent_model.model_id or (self.ctx.agent_model.model_config or {}).get("model_id")
        )
        
        self.ctx.instruction_builder = InstructionComposer(self.ctx.agent_model.system_prompt)

    async def _assemble_toolset(self, session_id: Optional[str], enable_search: Optional[bool], suggested_tools: List[str] = None):
        """装配工具并提取其专属指令 (支持基于 NLU 的渐进式加载)"""
        model_cfg = self.ctx.agent_model.model_config or {}
        search_flag = enable_search if enable_search is not None else model_cfg.get("enable_search", True)
        
        # 1. 加载所有工具 (基于 CapabilityRegistry + Tools RAG 推荐)
        self.ctx.tools = await default_tools.load_tools(
            self.ctx.agent_model, 
            self.db, 
            session_id, 
            enable_search=search_flag,
            suggested_tools=suggested_tools
        )
        
        # 2. 提取带有契约的工具指令 (统一接口处理)
        for tool in self.ctx.tools:
            if isinstance(tool, ToolWithPrompt):
                try:
                    snippet = tool.get_system_prompt_snippet()
                    if snippet:
                        self.ctx.instruction_builder.with_file_skill(snippet)
                except Exception as e:
                    logger.warning(f"Metadata extraction failed for tool {type(tool).__name__}: {e}")

    def _orchestrate_instructions(self) -> str:
        """指令编排逻辑：控制 Agent 的行为边界"""
        builder = self.ctx.instruction_builder
        model = self.ctx.agent_model
        
        if isinstance(model.instructions, list):
            for i, inst in enumerate(model.instructions):
                builder.add_segment(InstructionSegment(
                    key=f"raw_inst_{i}_{hash(inst)}",
                    content=inst,
                    category=InstructionCategory.SKILL
                ))

        if settings.OPENCLAW_BASE_URL:
            builder.with_openclaw()
        
        skills_cfg = model.skills_config or {}
        if skills_cfg.get("sandbox", {}).get("enabled"): 
            builder.with_sandbox()
            
        if model.knowledge_config: 
            builder.with_knowledge()

        builder.with_strategies(
            cot=bool(model.enable_cot),
            react=bool(model.enable_react)
        )
        builder.with_visualization()
            
        return builder.build()

    def _prepare_agno_params(self, instructions: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """参数转换层：将领域模型转换为 Agno 框架参数"""
        model = self.ctx.agent_model
        llm = self.ctx.llm_model
        
        # 规避推理冲突：若底层模型已是推理模型 (o1/R1)，则禁用 Agno 的逻辑层推理，防止输出冗余
        is_reasoning_model = getattr(llm, "is_reasoning_model", False)
        reasoning_enabled = overrides.get("reasoning_override")
        if reasoning_enabled is None:
            reasoning_enabled = False if is_reasoning_model else (model.enable_react is not True)

        return {
            "name": model.name,
            "role": model.description,
            "instructions": instructions,
            "tools": self.ctx.tools,
            "model": llm.model_id,
            "reasoning": reasoning_enabled,
            "markdown": model.enable_markdown,
            "memory": overrides.get("memory"),
            "storage": overrides.get("storage"),
            "knowledge": overrides.get("knowledge"),
            "user_id": overrides.get("user_id"),
            "enable_user_memories": overrides.get("enable_user_memories"),
            "add_memories_to_context": overrides.get("add_memories_to_context"),
            "show_tool_calls": False,  # Force disable raw text tool calls in stream
        }

    async def _finalize_instance(self, params: Dict[str, Any]) -> AgnoAgent:
        """实例化 Agent 并注入监控与元数据"""
        # 这里可以使用已有的 AgentFactory
        from app.services.agent.orchestration.factory import AgentFactory
        
        # 转换内部 config 对象
        from app.services.agent.domain.config import AgentConfig
        config = AgentConfig(**params) 

        agent = await AgentFactory.create_agent(
            config=config,
            db=self.db,
            llm_model=self.ctx.llm_model,
            **params
        )
        
        # 注入运行时元数据，方便调试和日志追踪
        agent.extra_metadata = {
            "agent_id": self.ctx.agent_id,
            "model_provider": self.ctx.llm_model.provider,
            "build_timestamp": asyncio.get_event_loop().time()
        }
        
        return agent
