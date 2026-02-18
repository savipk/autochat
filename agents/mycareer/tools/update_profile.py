"""
Update profile tool -- Mocked implementation.
Copied AS IS from tpchat/src/tools.py.
"""

from typing import Any

from langchain_core.tools import tool


@tool
def update_profile(section: str = "skills") -> dict:
    """Updates sections of the user's profile. Currently only skills can be added/edited."""
    raise RuntimeError("update_profile requires a profile; use run_update_profile instead")


def run_update_profile(
    profile: dict[str, Any],
    section: str = "skills",
    updates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Actual implementation that receives profile from the agent context."""
    if section != "skills":
        return {
            "success": False,
            "error": f"Update for section '{section}' is not yet supported.",
            "supported_sections": ["skills"]
        }

    if not updates:
        updates = {
            "topSkills": ["A2A", "MCP", "RAG"],
            "additionalSkills": ["Context Engineering", "Azure Open AI", "Azure AI Search"]
        }

    return {
        "success": True,
        "section": section,
        "updated_fields": updates,
        "previous_completion_score": profile.get("core", {}).get("completionScore", 0),
        "estimated_new_score": min(100, profile.get("core", {}).get("completionScore", 0) + 15)
    }
