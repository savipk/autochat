"""
Dynamic prompt middleware for profile-based personalization.

Loads the user profile directly from disk (via ``core.profile``) and
appends user context to the system prompt.  Only ``completion_score``
is read from the runtime context since it is a computed metric cached
in the session.
"""

from langchain.agents.middleware import dynamic_prompt

from core.profile import load_profile


def _get_context(request):
    """Extract context from request runtime (e.g. from ainvoke(..., context=...))."""
    return getattr(getattr(request, "runtime", None), "context", None)


@dynamic_prompt
async def personalization_middleware(request):
    """Appends user profile context to the system prompt at runtime."""
    profile = load_profile()
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

    context = _get_context(request)
    completion_score = getattr(context, "completion_score", None) if context else None
    if completion_score is not None:
        parts.append(f"Profile Completion: {completion_score}%")

    base = request.system_prompt or ""
    return (base + "\n" + "\n".join(parts)) if base else "\n".join(parts)
