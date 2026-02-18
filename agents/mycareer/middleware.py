"""
MyCareer-specific middleware.
"""

from langchain.agents.middleware import dynamic_prompt, wrap_tool_call

from core.config import PROFILE_LOW_COMPLETION_THRESHOLD


@dynamic_prompt
async def mycareer_personalization(state, context, config):
    """Appends user profile context to the system prompt at runtime."""
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


@wrap_tool_call
async def profile_warning_middleware(call, context, config):
    """
    Appends a warning to get_matches results when profile completion is < 50%.
    No tools are blocked -- the LLM decides what to call.
    """
    result = await call()
    tool_name = getattr(call, "tool_name", "")

    if tool_name == "get_matches":
        completion_score = getattr(context, "completion_score", 100) if context else 100
        if completion_score < PROFILE_LOW_COMPLETION_THRESHOLD:
            warning = (
                "\n\nNote: Your profile is less than 50% complete. "
                "Matching could be significantly better with a more complete profile. "
                "Consider adding skills, experience, or preferences."
            )
            if isinstance(result, dict):
                result["profile_warning"] = warning

    return result
