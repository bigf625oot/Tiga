from typing import List, Dict, Optional, Any
from agno.tools import Toolkit
from .skill import Skill
from .loaders.base import SkillLoader
from .loaders.local import LocalSkills
from .manager import Skills as SkillsManager

class SkillToolkit(Toolkit):
    """
    A Toolkit wrapper for the custom Skills system.
    This allows Skills to be used just like any other Agno Tool.
    """
    _name = "skills"
    _label = "扩展技能 (Skills)"
    _description = "访问和执行扩展技能包"
    
    def __init__(self, skills_path: str = "app/data/skills"):
        super().__init__(name="skills")
        self.skills_path = skills_path
        self.manager: Optional[SkillsManager] = None
        self._initialize_manager()

    def _initialize_manager(self):
        """Initialize the Skills Manager."""
        from pathlib import Path
        path = Path(self.skills_path)
        if not path.is_absolute():
            path = Path.cwd() / path
            
        if path.exists():
            loader = LocalSkills(path=str(path))
            self.manager = SkillsManager(loaders=[loader])
            # Register the tools provided by the manager
            for tool in self.manager.get_tools():
                # The manager returns agno.tools.function.Function objects
                # We need to register their entrypoints
                self.register(tool.entrypoint)
        else:
            # If path doesn't exist, we just don't register any tools
            pass

    def get_system_prompt_snippet(self) -> str:
        """Get the system prompt snippet for skills."""
        if self.manager:
            return self.manager.get_system_prompt_snippet()
        return ""

    def get_loaded_skills(self) -> List[Skill]:
        if self.manager:
            return self.manager.get_all_skills()
        return []
