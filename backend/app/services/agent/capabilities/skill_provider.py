import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from agno.tools import Toolkit
from .provider import CapabilityProvider
from app.models.skill import Skill as SkillModel
from app.services.agent.skills.toolkit import SkillToolkit
from app.services.agent.skills.skill import Skill as SkillObj

logger = logging.getLogger(__name__)

class SkillCapabilityProvider(CapabilityProvider):
    """
    Skill 能力提供者：将复杂的技能逻辑统一包装为标准的 Toolkit
    """
    
    def __init__(self, skills_config: Dict[str, Any], tools_config: List[Any], db: Optional[AsyncSession] = None):
        self.skills_config = skills_config or {}
        self.tools_config = tools_config or []
        self.db = db
        
    @property
    def provider_type(self) -> str:
        return "skill"
        
    async def get_tools(self) -> List[Toolkit]:
        file_skills_config = self.skills_config.get("file_skills", {})
        skills_path_str = file_skills_config.get("path", "app/data/skills")

        # 提取 Allowed IDs/Names
        allowed_raw = self.skills_config.get("allowed", []) or []
        allowed_names, allowed_ids = self._parse_allowed_items(allowed_raw)

        # 兼容旧配置：从 tools_config 中提取 type=skill 的项
        if isinstance(self.tools_config, list):
            for tc in self.tools_config:
                if isinstance(tc, dict) and tc.get("type") == "skill":
                    if tc.get("id"): allowed_ids.append(str(tc["id"]))
                    if tc.get("name"): allowed_names.append(str(tc["name"]))

        allowed_names = list(dict.fromkeys([n for n in allowed_names if n]))
        allowed_ids = list(dict.fromkeys([i for i in allowed_ids if i]))
        
        should_enable = file_skills_config.get("enabled", False) or bool(allowed_names) or bool(allowed_ids)
        # 强制默认启用 SkillToolkit，否则在未配置 allowed_skills 时模型将拿不到 execute_skill 导致幻觉
        # if not should_enable:
        #     return []

        preloaded: List[SkillObj] = []
        resolved_names: List[str] = []
        
        # 并发友好：数据库查询抽象至 Loader 层
        if self.db is not None and (allowed_ids or allowed_names):
            from app.services.agent.skills.loaders.database import DatabaseLoader
            loader = DatabaseLoader(self.db, allowed_ids=allowed_ids, allowed_names=allowed_names)
            preloaded = await loader.aload()
            for s in preloaded:
                resolved_names.append(s.name)

        allowed_for_runtime = list(dict.fromkeys([n for n in (allowed_names + resolved_names) if n]))
        
        # P10 补丁：如果 enabled 为 True 但没有指定 allowed，我们传 None 给 allowed_skills，
        # 这会让 LocalSkills loader 默认加载 path 下所有的技能，而不是加载 0 个
        if not allowed_for_runtime and file_skills_config.get("enabled", False):
            allowed_for_runtime = None
            
        self.skill_toolkit = SkillToolkit(
            skills_path=skills_path_str,
            allowed_skills=allowed_for_runtime,
            skills=preloaded or None,
        )
        
        logger.info(f"Loaded SkillCapabilityProvider (allowed={len(allowed_for_runtime) if allowed_for_runtime else 'ALL'})")
        return [self.skill_toolkit]
        
    def get_system_prompt_snippet(self) -> Optional[str]:
        # 修复拓扑断层：确保底层 XML 规则无损上浮至大模型的 Context Window 中
        if hasattr(self, 'skill_toolkit') and self.skill_toolkit is not None:
            return self.skill_toolkit.get_system_prompt_snippet()
        return None

    def _parse_allowed_items(self, raw_list: List[Any]) -> tuple[List[str], List[str]]:
        names, ids = [], []
        for item in raw_list:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict):
                if item.get("id"): ids.append(str(item["id"]))
                if item.get("name"): names.append(str(item["name"]))
        return names, ids
