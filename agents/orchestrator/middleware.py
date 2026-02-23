"""
Orchestrator-specific middleware.
"""

from langchain.agents.middleware import dynamic_prompt


@dynamic_prompt
async def orchestrator_personalization(request):
    """Appends the user's first name to the system prompt so the LLM can use
    it in its opening welcome message.
    """
    context = getattr(getattr(request, "runtime", None), "context", None)
    first_name = getattr(context, "first_name", "") if context else ""

    base = request.system_prompt or ""
    if first_name:
        return base + f"\nUser's first name: {first_name}"
    return base
