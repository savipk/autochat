"""
JD Composer-specific middleware.
"""

from langchain.agents.middleware import dynamic_prompt


def _get_context(request):
    """Extract context from request runtime (e.g. from ainvoke(..., context=...))."""
    return getattr(getattr(request, "runtime", None), "context", None)


@dynamic_prompt
async def jd_composer_personalization(request):
    """Appends hiring manager context to the system prompt."""
    context = _get_context(request)
    if not context:
        return request.system_prompt or ""

    user_name = getattr(context, "user_name", "")
    department = getattr(context, "department", "")

    if not user_name and not department:
        return request.system_prompt or ""

    parts = ["\n\n--- Hiring Manager Context ---"]
    if user_name:
        parts.append(f"Name: {user_name}")
    if department:
        parts.append(f"Department: {department}")

    base = request.system_prompt or ""
    return (base + "\n" + "\n".join(parts)) if base else "\n".join(parts)
