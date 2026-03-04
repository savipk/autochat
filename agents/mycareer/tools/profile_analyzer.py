"""
Profile analyzer tool -- Functional implementation.
"""

import logging
from typing import Any

from langchain_core.tools import tool

from core.profile import load_profile
from core.profile_schema import SECTION_REGISTRY
from core.profile_score import compute_completion_score, compute_section_scores, get_missing_sections

logger = logging.getLogger("chatbot.tools")

PROFILE_COMPLETION_THRESHOLD = 80


@tool
def profile_analyzer(completion_threshold: int = PROFILE_COMPLETION_THRESHOLD) -> dict:
    """Analyzes the user's profile to provide a completion score based on missing
    or insufficient information. Determines if the profile is complete enough for
    job matching and provides insights and recommended next actions."""
    return run_profile_analyzer(completion_threshold=completion_threshold)


def run_profile_analyzer(completion_threshold: int = PROFILE_COMPLETION_THRESHOLD) -> dict[str, Any]:
    """Analyze the profile loaded from the configured data path."""
    if not isinstance(completion_threshold, int) or completion_threshold < 0 or completion_threshold > 100:
        return {"success": False, "error": "completion_threshold must be an integer between 0 and 100."}

    profile = load_profile()
    core = profile.get("core", {})

    completion_score = compute_completion_score(profile)
    section_scores = compute_section_scores(profile)
    missing_keys = get_missing_sections(profile)

    insights: list[dict[str, Any]] = []

    # Map storage_key → (observation, action, recommendation)
    _insight_map = {
        "experience": (
            "No work experience found",
            "update_profile_field",
            "Add at least one job with title, company, and dates",
        ),
        "qualification": (
            "Missing educational or certification details",
            "update_profile_field",
            "Add a degree or certification",
        ),
        "skills": (
            "No top or additional skills detected",
            "infer_skills",
            "Infer or manually add top 5 skills",
        ),
        "careerAspirationPreference": (
            "Career aspiration preferences missing",
            "set_preferences",
            "Add preferred career aspirations",
        ),
        "careerLocationPreference": (
            "Relocation preferences missing",
            "set_preferences",
            "Add preferred relocation regions or indicate relocation preference",
        ),
        "careerRolePreference": (
            "Preferred roles missing",
            "set_preferences",
            "Add preferred roles or role classifications",
        ),
        "language": (
            "No language proficiency data found",
            "update_profile_field",
            "Add at least one language with proficiency level",
        ),
    }

    for key in missing_keys:
        if key in _insight_map:
            obs, action, rec = _insight_map[key]
            insights.append({
                "area": key,
                "observation": obs,
                "action": action,
                "recommendation": rec,
            })

    next_actions = []
    if completion_score < completion_threshold:
        for i, insight in enumerate(insights, start=1):
            next_actions.append({
                "title": insight["recommendation"],
                "tool": insight["action"],
                "priority": i,
            })
    else:
        next_actions = [
            {"title": "Find Job Matches", "tool": "get_matches", "priority": 1},
            {"title": "Ask about a Job", "tool": "ask_jd_qa", "priority": 2},
        ]

    return {
        "success": True,
        "error": None,
        "completionScore": completion_score,
        "sectionScores": section_scores,
        "missingSections": missing_keys,
        "insights": insights,
        "nextActions": next_actions,
    }
