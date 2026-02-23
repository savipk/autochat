"""
MyCareer-specific middleware.
"""

from langchain.agents.middleware import dynamic_prompt, wrap_tool_call
from langchain_core.messages import ToolMessage

from core.config import PROFILE_LOW_COMPLETION_THRESHOLD
from core.profile import load_profile
from core.middleware.user_identity import get_user_identity

# Maps thread_id → completion_score; populated on first touch per thread.
_thread_analysis: dict[str, int] = {}


def _get_context(request):
    """Extract context from request runtime (e.g. from ainvoke(..., context=...))."""
    return getattr(getattr(request, "runtime", None), "context", None)


def _get_completion_score(thread_id: str, context) -> int | None:
    """Return completion_score from the dict if available, else from context."""
    if thread_id in _thread_analysis:
        return _thread_analysis[thread_id]
    return getattr(context, "completion_score", None) if context else None


@dynamic_prompt
async def first_touch_profile_middleware(request):
    """Runs profile analyzer on first touch and injects a summary into the system prompt.

    On subsequent calls for the same thread the prompt is returned unchanged so
    the expensive analysis only fires once per session.
    """
    context = _get_context(request)
    thread_id = getattr(context, "thread_id", "") if context else ""
    base = request.system_prompt or ""

    if thread_id and thread_id not in _thread_analysis:
        from agents.mycareer.tools.profile_analyzer import run_profile_analyzer

        analysis = run_profile_analyzer()
        score = analysis.get("completionScore", 100)
        _thread_analysis[thread_id] = score

        missing = analysis.get("missingSections", [])
        insights = analysis.get("insights", [])

        summary_parts = ["\n\n--- Profile Analysis (First Touch) ---"]
        summary_parts.append(f"Completion Score: {score}%")
        if missing:
            summary_parts.append(f"Missing sections: {', '.join(missing)}")
        if insights:
            recommendations = [i.get("recommendation", "") for i in insights[:3]]
            top_recs = "; ".join(r for r in recommendations if r)
            if top_recs:
                summary_parts.append(f"Top recommendations: {top_recs}")

        return (base + "\n" + "\n".join(summary_parts)) if base else "\n".join(summary_parts)

    return base


@dynamic_prompt
async def mycareer_personalization(request):
    """Appends user profile context to the system prompt at runtime."""
    profile = load_profile()
    if not profile:
        return request.system_prompt or ""

    identity = get_user_identity(profile)

    parts = ["\n\n--- User Context ---"]
    if identity["name"]:
        parts.append(f"Name: {identity['name']}")
    if identity["job_title"]:
        parts.append(f"Title: {identity['job_title']}")
    if identity["rank"]:
        parts.append(f"Level: {identity['rank']}")
    if identity["top_skills"]:
        parts.append(f"Top Skills: {', '.join(identity['top_skills'])}")

    context = _get_context(request)
    thread_id = getattr(context, "thread_id", "") if context else ""
    completion_score = _get_completion_score(thread_id, context)
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
        thread_id = getattr(context, "thread_id", "") if context else ""
        completion_score = _get_completion_score(thread_id, context)
        if completion_score is None:
            completion_score = 100
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
