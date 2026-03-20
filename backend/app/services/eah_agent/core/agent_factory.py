import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Type
from dataclasses import dataclass, field

from agno.agent import Agent
from sqlalchemy.ext.asyncio import AsyncSession

# 内部模块依赖
from app.core.config import settings
from app.models.llm_model import LLMModel
from app.services.llm.factory import ModelFactory
from app.services.llm.resolver import resolve_chat_llm_model
from app.services.eah_agent.domain.config import AgentConfig, TeamConfig
from app.services.eah_agent.tools.tool_factory import ToolFactory
from app.services.eah_agent.skills.loaders.local import LocalSkills
from app.services.eah_agent.skills.manager import Skills
from app.services.eah_agent.utils.secret_refs import resolve_secret_refs
from app.services.eah_agent.utils.agno_compat import filter_init_kwargs

logger = logging.getLogger(__name__)

# --- 1. 指令编排器 (Instruction Orchestrator) ---

class InstructionManager:
    """处理复杂指令的聚合、去重与格式化"""
    def __init__(self, base: Optional[Union[str, List[str]]] = None):
        self._items: List[str] = []
        if base:
            self.extend(base)

    def append(self, item: Optional[str]):
        if item and item.strip() and item not in self._items:
            self._items.append(item.strip())

    def extend(self, items: Union[str, List[str]]):
        if isinstance(items, str):
            self.append(items)
        else:
            for i in items: self.append(i)

    def compile(self) -> List[str]:
        return self._items

# --- 2. 模型适配器 (Model Provider Adapter) ---

class ModelProviderAdapter:
    """解耦厂商特定的逻辑 (DeepSeek, OpenAI o1, etc.)"""
    @staticmethod
    def apply_custom_logic(model: Any, llm_record: LLMModel, config: AgentConfig):
        provider = (llm_record.provider or "").lower()
        
        # DeepSeek R1/V3 推理增强逻辑
        if provider == "deepseek" and config.reasoning:
            # 动态设置厂商特有参数，避免硬编码在工厂主流程
            attrs = {
                "extra_body": {"thinking": {"type": "enabled"}},
                "reasoning_effort": "high",
                "verbosity": "high"
            }
            for attr, val in attrs.items():
                if hasattr(model, attr):
                    setattr(model, attr, val)
        
        # 未来可在此扩展 OpenAI o1-preview 或 Claude 3.5 Sonnet 的特殊处理

# --- 3. 核心 Agent 工厂 (The Grand Factory) ---

class AgentFactory:
    """
    P10 级 Agent 工厂：支持高并发构建、多态模型适配与指令深度编排。
    """
    
    _skills_manager: Optional[Skills] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_skills_manager(cls) -> Optional[Skills]:
        """单例模式加载技能管理器"""
        if cls._skills_manager is None:
            async with cls._lock:
                if cls._skills_manager is None:
                    path = Path(__file__).parent.parent / "skills"
                    if path.exists():
                        loader = LocalSkills(str(path), validate=False)
                        cls._skills_manager = Skills([loader])
                    else:
                        logger.warning(f"Skills path missing: {path}")
        return cls._skills_manager

    @staticmethod
    async def create_agent(
        config: AgentConfig, 
        db: Optional[AsyncSession] = None, 
        llm_model: Optional[LLMModel] = None,
        tools: Optional[list] = None,
        instructions: Optional[Union[list, str]] = None,
        **kwargs
    ) -> Agent:
        """
        构建单个 Agno Agent。
        """
        try:
            # 1. 模型资源解析 (Resource Resolution)
            if not llm_model and db:
                llm_model = await resolve_chat_llm_model(db, model_id=config.model_id)
            
            if not llm_model:
                llm_model = ModelFactory.resolve_default_llm_model(settings)

            # 2. 模型实例化与适配 (Model Instantiation & Adaptation)
            model_instance = ModelFactory.create_model(llm_model)
            # 注入配置参数
            if config.model_params:
                for k, v in config.model_params.items():
                    if hasattr(model_instance, k): setattr(model_instance, k, v)
            
            # 应用厂商特定策略
            ModelProviderAdapter.apply_custom_logic(model_instance, llm_model, config)

            # 3. 工具与技能装配 (Tooling & Skills)
            final_tools = tools or []
            im = InstructionManager(instructions or config.instructions)

            # 异步加载技能 (Skills are semi-static)
            sm = await AgentFactory.get_skills_manager()
            if config.skills and sm:
                final_tools.extend(sm.get_tools())
                im.append(sm.get_system_prompt_snippet())

            # 加载动态工具 (ToolFactory)
            if config.tools:
                ToolFactory.initialize()
                for tc in config.tools:
                    if not tc.enabled: continue
                    t_inst = ToolFactory.create_tool(tc.name, resolve_secret_refs(tc.config or {}))
                    if t_inst: final_tools.append(t_inst)

            # 4. 实例封装 (Final Assembly)
            agent_payload = {
                "name": config.name,
                "model": model_instance,
                "description": config.role,
                "instructions": im.compile(),
                "tools": final_tools,
                "show_tool_calls": config.model_params.get("show_tool_calls", True),
                "markdown": kwargs.pop("markdown", True),
                "reasoning": config.reasoning,
                "monitoring": True,
                "debug_mode": settings.DEBUG,
                **kwargs,
            }

            # 过滤 Agno 构造函数参数，防止 SDK 升级崩溃
            agent = Agent(**filter_init_kwargs(Agent.__init__, agent_payload))
            
            # 注入元数据用于 Trace
            agent.extra_metadata = {"model_id": llm_model.model_id, "provider": llm_model.provider}
            
            return agent

        except Exception as e:
            logger.error(f"Failed to create agent [{config.name}]: {e}", exc_info=True)
            raise

    @staticmethod
    async def create_team(config: TeamConfig, db: Optional[AsyncSession] = None) -> Agent:
        """
        P10 级团队构建：支持成员并行实例化，自动生成协作提示词。
        """
        try:
            # 1. 并行构建所有成员 (Concurrency Optimization)
            # 相比于 for 循环，并行构建能显著降低复杂团队的启动延迟
            member_tasks = [
                AgentFactory.create_agent(m_cfg, db=db) 
                for m_cfg in config.members
            ]
            members = await asyncio.gather(*member_tasks)

            # 2. 构建 Leader
            leader_agent = await AgentFactory.create_agent(config.leader_agent, db=db)
            
            # 3. 编排团队逻辑
            leader_agent.team = members
            
            # 4. 自动生成增强型团队指令 (Team Orchestration Prompt)
            member_context = "\n".join([f"- {m.name}: {m.description}" for m in members])
            team_prompt = (
                f"\n\n## Team Collaboration\n"
                f"You are the Leader. Coordinate the following specialists:\n{member_context}\n"
                f"Delegate tasks by calling their respective names when needed."
            )
            
            # 注入指令
            if isinstance(leader_agent.instructions, list):
                leader_agent.instructions.append(team_prompt)
            else:
                leader_agent.instructions = f"{leader_agent.instructions or ''}\n{team_prompt}"

            return leader_agent

        except Exception as e:
            logger.error(f"Team construction failed [{config.name}]: {e}", exc_info=True)
            raise