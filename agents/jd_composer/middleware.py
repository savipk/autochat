"""
JD Composer-specific middleware.
"""

from langchain.agents import dynamic_prompt


@dynamic_prompt
async def jd_composer_personalization(state, context, config):
    """Appends hiring manager context to the system prompt."""
    if not context:
        return None

    user_name = getattr(context, "user_name", "")
    department = getattr(context, "department", "")

    if not user_name and not department:
        return None

    parts = ["\n\n--- Hiring Manager Context ---"]
    if user_name:
        parts.append(f"Name: {user_name}")
    if department:
        parts.append(f"Department: {department}")

    return "\n".join(parts)
