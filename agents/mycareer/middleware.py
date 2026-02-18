"""
MyCareer-specific middleware.
"""

from langchain.agents.middleware import dynamic_prompt, wrap_tool_call
from langchain_core.messages import ToolMessage

from core.config import PROFILE_LOW_COMPLETION_THRESHOLD


def _get_context(request):
    """Extract context from request runtime (e.g. from ainvoke(..., context=...))."""
    return getattr(getattr(request, "runtime", None), "context", None)


@dynamic_prompt
async def mycareer_personalization(request):
    """Appends user profile context to the system prompt at runtime."""
    context = _get_context(request)
    profile = getattr(context, "profile", {}) if context else {}
    if not profile:
        return request.system_prompt or ""

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

    base = request.system_prompt or ""
    return (base + "\n" + "\n".join(parts)) if base else "\n".join(parts)


@wrap_tool_call
async def profile_warning_middleware(request, handler):
    """
    Appends a warning to get_matches results when profile completion is < 50%.
    No tools are blocked -- the LLM decides what to call.
    """
    result = await handler(request)
    tool_name = request.tool_call.get("name", "")

    if tool_name == "get_matches":
        context = _get_context(request)
        completion_score = getattr(context, "completion_score", 100) if context else 100
        if completion_score < PROFILE_LOW_COMPLETION_THRESHOLD:
            warning = (
                "\n\nNote: Your profile is less than 50% complete. "
                "Matching could be significantly better with a more complete profile. "
                "Consider adding skills, experience, or preferences."
            )
            if isinstance(result, ToolMessage):
                content = result.content if isinstance(result.content, str) else str(result.content)
                result = ToolMessage(
                    content=content + warning,
                    tool_call_id=result.tool_call_id,
                    name=result.name,
                )

    return result
