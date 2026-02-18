"""
Skill dataclass and registry for on-demand knowledge loading.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Skill:
    """A prompt-driven specialization loaded on demand."""
    name: str
    description: str = ""
    path: str = ""
    tags: list[str] = field(default_factory=list)
    _content_cache: str | None = field(default=None, repr=False)

    def load_content(self) -> str:
        if self._content_cache is not None:
            return self._content_cache
        if not self.path or not os.path.exists(self.path):
            return f"Skill '{self.name}' content not found at {self.path}"
        with open(self.path, "r", encoding="utf-8") as f:
            self._content_cache = f.read()
        return self._content_cache


class SkillRegistry:
    """Registry of available skills for an agent."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list_skills(self) -> list[dict[str, str]]:
        return [
            {"name": s.name, "description": s.description}
            for s in self._skills.values()
        ]

    def __contains__(self, name: str) -> bool:
        return name in self._skills
