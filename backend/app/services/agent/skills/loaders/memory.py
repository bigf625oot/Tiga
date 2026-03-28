from typing import List
from .base import SkillLoader
from ..skill import Skill


class InMemorySkills(SkillLoader):
    def __init__(self, skills: List[Skill]):
        self._skills = skills

    def load(self) -> List[Skill]:
        return list(self._skills)

