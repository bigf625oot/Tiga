import asyncio
import logging
from typing import Optional, Union, Any

from agno.agent import Agent

# 内部模块依赖
from app.core.config import settings
from app.models.llm_model import LLMModel
from app.services.llm.factory import ModelFactory
from app.services.eah_agent.domain.config import AgentConfig, TeamConfig
from app.services.eah_agent.utils.agno_compat import filter_init_kwargs

logger = logging.getLogger(__name__)

class ModelProviderAdapter:
    """解耦厂商特定的逻辑 (DeepSeek, OpenAI o1, etc.)"""
    @staticmethod
    def apply_custom_logic(model: Any, llm_record: LLMModel, config: AgentConfig):
        provider = (llm_record.provider or "").lower()
        
        reasoning = getattr(config, 'reasoning', False) or getattr(getattr(config, 'llm', None), 'reasoning', False)
        
        # DeepSeek R1/V3 推理增强逻辑
        if provider == "deepseek" and reasoning:
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

class AgentFactory:
    """
    P10 级 Agent 工厂：支持高并发构建、多态模型适配。
    注意：此层已纯化，不处理指令编排与 DB 解析，所有依赖需由外部(Assembler)注入。
    """
    
    @staticmethod
    async def create_agent(
        config: AgentConfig, 
        llm_model: LLMModel,
        tools: Optional[list] = None,
        instructions: Optional[Union[list, str]] = None,
        **kwargs
    ) -> Agent:
        """
        构建单个 Agno Agent。
        """
        try:
            if not llm_model:
                llm_model = ModelFactory.resolve_default_llm_model(settings)

            model_instance = ModelFactory.create_model(llm_model)
            model_params = getattr(config, "model_params", {})
            if model_params:
                for k, v in model_params.items():
                    if hasattr(model_instance, k):
                        setattr(model_instance, k, v)
            
            ModelProviderAdapter.apply_custom_logic(model_instance, llm_model, config)

            # 避免将 model 强行注入导致与 model_instance 冲突
            kwargs.pop("model", None)
            
            agent_payload = {
                "name": config.name,
                "model": model_instance,
                "description": config.role or config.description,
                "instructions": instructions or config.instructions or getattr(config, "system_prompt", []),
                "tools": tools or getattr(config, "tools", []),
                "show_tool_calls": True, # Force show_tool_calls to True so Agno passes tools to LLM
                "markdown": kwargs.pop("markdown", True),
                "reasoning": getattr(config, "reasoning", False) or getattr(getattr(config, "llm", None), "reasoning", False),
                "monitoring": True,
                "debug_mode": settings.DEBUG,
                **kwargs,
            }

            # 过滤 Agno 构造函数参数，防止 SDK 升级引发异常
            agent = Agent(**filter_init_kwargs(Agent.__init__, agent_payload))
            
            agent.extra_metadata = {"model_id": llm_model.model_id, "provider": llm_model.provider}
            
            return agent

        except Exception as e:
            logger.error(f"Failed to create agent [{config.name}]: {e}", exc_info=True)
            raise

    @staticmethod
    async def create_team(config: TeamConfig, llm_model: LLMModel) -> Agent:
        """
        P10 级团队构建：支持成员并行实例化，自动生成协作提示词。
        """
        try:
            # 相比于 for 循环，并行构建能显著降低复杂团队的启动延迟
            member_tasks = [
                AgentFactory.create_agent(m_cfg, llm_model=llm_model) 
                for m_cfg in config.members
            ]
            members = await asyncio.gather(*member_tasks)

            leader_agent = await AgentFactory.create_agent(config.leader, llm_model=llm_model)
            leader_agent.team = members
            
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