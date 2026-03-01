"""
Update profile tool -- supports all editable profile sections with persistence.
"""

from typing import Any

import chainlit as cl
from langchain_core.tools import tool

from core.profile import load_profile
from core.profile_manager import ProfileManager

VALID_SECTIONS = [
    "skills",
    "experience",
    "education",
    "careerAspirationPreference",
    "careerLocationPreference",
    "careerRolePreference",
    "language",
]


def _get_user_context() -> tuple[str, str]:
    """Extract username and profile_path from the Chainlit session."""
    try:
        user = cl.user_session.get("user")
        if user and hasattr(user, "metadata") and user.metadata:
            return user.identifier, user.metadata.get("profile_path", "")
    except Exception:
        pass
    return "", ""


def _compute_completion_score(profile: dict) -> int:
    """Compute a simple completion score based on section presence."""
    core = profile.get("core", {})
    sections = {
        "experience": bool((core.get("experience") or {}).get("experiences")),
        "education": bool((core.get("qualification") or {}).get("educations")),
        "skills": bool(core.get("skills", {}).get("top") or core.get("skills", {}).get("additional")),
        "aspirations": bool((core.get("careerAspirationPreference") or {}).get("preferredAspirations")),
        "location": bool(core.get("careerLocationPreference")),
        "roles": bool((core.get("careerRolePreference") or {}).get("preferredRoles")),
        "language": bool((core.get("language") or {}).get("languages")),
    }
    filled = sum(1 for v in sections.values() if v)
    return round(filled / len(sections) * 100)


@tool
def update_profile(section: str = "skills", updates: dict | None = None) -> dict:
    """Updates sections of the user's profile.

    Args:
        section: The profile section to update. Supported: skills, experience,
                 education, careerAspirationPreference, careerLocationPreference,
                 careerRolePreference, language.
        updates: Dict with section-specific updates. For skills, pass
                 {"skills": ["Python", "Docker", ...]} as a flat list, or
                 {"topSkills": [...], "additionalSkills": [...]} for explicit placement.
    """
    return run_update_profile(section=section, updates=updates)


def run_update_profile(
    section: str = "skills",
    updates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Actual implementation -- loads profile, applies updates, persists via ProfileManager."""
    if not section or not isinstance(section, str):
        return {"success": False, "error": "section is required and must be a non-empty string."}

    if section not in VALID_SECTIONS:
        return {
            "success": False,
            "error": f"Update for section '{section}' is not yet supported. Supported: {VALID_SECTIONS}",
        }

    username, profile_path = _get_user_context()
    profile = load_profile(profile_path or None)
    prev_score = _compute_completion_score(profile)

    if not updates:
        if section == "skills":
            updates = {
                "topSkills": ["A2A", "MCP", "RAG"],
                "additionalSkills": ["Context Engineering", "Azure Open AI", "Azure AI Search"],
            }
        else:
            return {"success": False, "error": "updates dict is required for non-skills sections."}

    # Normalize flat skills list
    if section == "skills" and "skills" in updates and isinstance(updates["skills"], list):
        flat = updates["skills"]
        updates = {
            "topSkills": flat[:3],
            "additionalSkills": flat[3:],
        }

    # Apply updates to profile
    core = profile.setdefault("core", {})
    if section == "skills":
        core.setdefault("skills", {})
        if "topSkills" in updates:
            core["skills"]["top"] = updates["topSkills"]
        if "additionalSkills" in updates:
            core["skills"]["additional"] = updates["additionalSkills"]
    elif section == "experience":
        core["experience"] = updates
    elif section == "education":
        core["qualification"] = updates
    else:
        core[section] = updates

    # Persist if we have user context
    if username and profile_path:
        mgr = ProfileManager(username=username, profile_path=profile_path)
        mgr.submit(profile)

    new_score = _compute_completion_score(profile)

    return {
        "success": True,
        "error": None,
        "section": section,
        "updated_fields": updates,
        "previous_completion_score": prev_score,
        "estimated_new_score": new_score,
        "profile_path": profile_path,
        "username": username,
    }
