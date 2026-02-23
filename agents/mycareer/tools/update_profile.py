"""
Update profile tool -- Mocked implementation.
"""

from typing import Any

from langchain_core.tools import tool

from core.profile import load_profile

VALID_SECTIONS = ["skills"]


@tool
def update_profile(section: str = "skills") -> dict:
    """Updates sections of the user's profile. Currently only skills can be added/edited."""
    return run_update_profile(section=section)


def run_update_profile(
    section: str = "skills",
    updates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Actual implementation -- loads profile from the configured data path."""
    if not section or not isinstance(section, str):
        return {"success": False, "error": "section is required and must be a non-empty string."}

    if section not in VALID_SECTIONS:
        return {
            "success": False,
            "error": f"Update for section '{section}' is not yet supported. Supported: {VALID_SECTIONS}",
        }

    if not updates:
        updates = {
            "topSkills": ["A2A", "MCP", "RAG"],
            "additionalSkills": ["Context Engineering", "Azure Open AI", "Azure AI Search"]
        }

    profile = load_profile()
    prev_score = profile.get("completionScore", 0)

    return {
        "success": True,
        "error": None,
        "section": section,
        "updated_fields": updates,
        "previous_completion_score": prev_score,
        "estimated_new_score": min(100, prev_score + 15)
    }
