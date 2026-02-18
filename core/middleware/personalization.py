"""
Dynamic prompt middleware for profile-based personalization.
"""

from langchain.agents.middleware import dynamic_prompt


@dynamic_prompt
async def personalization_middleware(state, context, config):
    """
    Appends user profile context to the system prompt at runtime.
    The base system prompt is set on the agent; this adds profile info dynamically.
    """
    profile = getattr(context, "profile", {}) if context else {}
    if not profile:
        return None

    core = profile.get("core", {})
    name_info = core.get("name", {})
    user_name = f"{name_info.get('businessFirstName', '')} {name_info.get('businessLastName', '')}".strip()
    job_title = core.get("businessTitle", "")
    rank = core.get("rank", "")

    skills = profile.get("skills", {})
    top_skills = skills.get("top", []) if isinstance(skills, dict) else []
    skill_names = [s.get("name", s) if isinstance(s, dict) else str(s) for s in top_skills[:5]]

    parts = ["\n\n--- User Context ---"]
    if user_name:
        parts.append(f"Name: {user_name}")
    if job_title:
        parts.append(f"Title: {job_title}")
    if rank:
        parts.append(f"Level: {rank}")
    if skill_names:
        parts.append(f"Top Skills: {', '.join(skill_names)}")

    completion_score = getattr(context, "completion_score", None)
    if completion_score is not None:
        parts.append(f"Profile Completion: {completion_score}%")

    return "\n".join(parts)
