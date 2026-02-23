"""
Dynamic prompt middleware for hiring-manager personalization.

Loads the user profile from disk (via ``core.profile``) and appends
hiring-manager context (name, title, level) to the system prompt.
"""

from langchain.agents.middleware import dynamic_prompt

from core.profile import load_profile
from core.middleware.user_identity import get_user_identity


@dynamic_prompt
async def jd_generator_personalization(request):
    """Appends hiring-manager context to the system prompt at runtime."""
    profile = load_profile()
    if not profile:
        return request.system_prompt or ""

    identity = get_user_identity(profile)

    parts = ["\n\n--- Hiring Manager Context ---"]
    if identity["name"]:
        parts.append(f"Name: {identity['name']}")
    if identity["job_title"]:
        parts.append(f"Title: {identity['job_title']}")
    if identity["rank"]:
        parts.append(f"Level: {identity['rank']}")

    if len(parts) == 1:
        return request.system_prompt or ""

    base = request.system_prompt or ""
    return (base + "\n" + "\n".join(parts)) if base else "\n".join(parts)
