from typing import List, Optional, Iterable, Set
import json
from agno.tools import Toolkit
from .skill import Skill
from .loaders.local import LocalSkills
from .loaders.memory import InMemorySkills
from .manager import Skills as SkillsManager

class SkillToolkit(Toolkit):
    """
    A Toolkit wrapper for the custom Skills system.
    This allows Skills to be used just like any other Agno Tool.
    """
    _name = "skills"
    _label = "扩展技能 (Skills)"
    _description = "访问和执行扩展技能包"
    
    def __init__(
        self,
        skills_path: str = "app/data/skills",
        allowed_skills: Optional[Iterable[str]] = None,
        skills: Optional[List[Skill]] = None,
    ):
        super().__init__(name="skills")
        self.skills_path = skills_path
        self.manager: Optional[SkillsManager] = None
        self.allowed: Optional[Set[str]] = set(allowed_skills) if allowed_skills else None
        self._preloaded_skills = skills
        self._initialize_manager()

    def _initialize_manager(self):
        """Initialize the Skills Manager."""
        from pathlib import Path
        path = Path(self.skills_path)
        if not path.is_absolute():
            path = Path.cwd() / path
            
        loaders = []
        if self._preloaded_skills is not None:
            loaders.append(InMemorySkills(self._preloaded_skills))
        if path.exists():
            loaders.append(LocalSkills(path=str(path)))
        if not loaders:
            return
        self.manager = SkillsManager(loaders=loaders, allowed_skills=self.allowed)

        # Register standard tools from manager directly
        for tool in self.manager.get_tools():
            self.register(tool)

    def get_system_prompt_snippet(self) -> str:
        """Get the system prompt snippet for skills."""
        if self.manager:
            return self.manager.get_system_prompt_snippet()
        return ""

    def get_loaded_skills(self) -> List[Skill]:
        if self.manager:
            return self.manager.get_all_skills()
        return []
