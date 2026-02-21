"""
MyCareer-specific middleware.
"""

from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage

from core.config import PROFILE_LOW_COMPLETION_THRESHOLD
from core.middleware.personalization import personalization_middleware as mycareer_personalization  # noqa: F401


def _get_context(request):
    """Extract context from request runtime (e.g. from ainvoke(..., context=...))."""
    return getattr(getattr(request, "runtime", None), "context", None)


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
