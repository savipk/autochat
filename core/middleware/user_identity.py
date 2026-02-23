"""
Shared helper for extracting user identity fields from a profile dict.

Import ``get_user_identity`` instead of duplicating profile-field
extraction across middleware modules.
"""


def get_user_identity(profile: dict) -> dict:
    """Return a flat dict of common identity fields from a raw profile.

    Returns:
        {
            "name": str,       # "First Last" (may be empty)
            "job_title": str,
            "rank": str,
            "top_skills": list[str],  # up to 5
        }
    """
    core = profile.get("core", {})
    name_info = core.get("name", {})
    name = f"{name_info.get('businessFirstName', '')} {name_info.get('businessLastName', '')}".strip()
    job_title = core.get("businessTitle", "")
    rank = core.get("rank", "")

    skills = profile.get("skills", {})
    top_skills_raw = skills.get("top", []) if isinstance(skills, dict) else []
    top_skills = [
        s.get("name", s) if isinstance(s, dict) else str(s)
        for s in top_skills_raw[:5]
    ]

    return {
        "name": name,
        "job_title": job_title,
        "rank": rank,
        "top_skills": top_skills,
    }
