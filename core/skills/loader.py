"""
Factory for creating a load_skill tool bound to a SkillRegistry.
"""

from langchain_core.tools import tool

from core.skills.base import SkillRegistry


def create_skill_loader_tool(registry: SkillRegistry):
    """Returns a @tool function that loads skill content by name."""

    @tool
    def load_skill(skill_name: str) -> str:
        """Load specialized knowledge or guidelines by skill name.
        Available skills can be listed by calling this tool with skill_name='list'.
        """
        if skill_name == "list":
            skills = registry.list_skills()
            if not skills:
                return "No skills available."
            lines = ["Available skills:"]
            for s in skills:
                lines.append(f"  - {s['name']}: {s['description']}")
            return "\n".join(lines)

        skill = registry.get(skill_name)
        if skill is None:
            available = [s["name"] for s in registry.list_skills()]
            return f"Skill '{skill_name}' not found. Available: {available}"

        return skill.load_content()

    return load_skill
