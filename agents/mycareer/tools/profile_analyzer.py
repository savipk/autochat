"""
Profile analyzer tool -- Functional implementation.
"""

import logging
from typing import Any

from langchain_core.tools import tool

from core.profile import load_profile

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
    score = 0
    missing_sections: list[str] = []
    insights: list[dict[str, Any]] = []
    section_scores: dict[str, int] = {}

    def has_items(value: Any) -> bool:
        if isinstance(value, list):
            return len(value) > 0
        return bool(value)

    exp_ok = has_items(profile.get("experience", {}).get("experiences", []))
    exp_score = 25 if exp_ok else 0
    score += exp_score
    section_scores["experience"] = exp_score
    if not exp_ok:
        missing_sections.append("experience")
        insights.append({
            "area": "experience",
            "observation": "No work experience found",
            "action": "update_profile_field",
            "recommendation": "Add at least one job with title, company, and dates"
        })

    qual_ok = has_items(profile.get("qualification", {}).get("educations", []))
    qual_score = 15 if qual_ok else 0
    score += qual_score
    section_scores["qualification"] = qual_score
    if not qual_ok:
        missing_sections.append("qualification")
        insights.append({
            "area": "qualification",
            "observation": "Missing educational or certification details",
            "action": "update_profile_field",
            "recommendation": "Add a degree or certification"
        })

    skills = profile.get("skills")
    if isinstance(skills, dict):
        skills_ok = has_items(skills.get("top", [])) or has_items(skills.get("additional", []))
    else:
        skills_ok = has_items(skills)
    skills_score = 20 if skills_ok else 0
    score += skills_score
    section_scores["skills"] = skills_score
    if not skills_ok:
        missing_sections.append("skills")
        insights.append({
            "area": "skills",
            "observation": "No top or additional skills detected",
            "action": "infer_skills",
            "recommendation": "Infer or manually add top 5 skills"
        })

    aspiration_ok = has_items(profile.get("careerAspirationPreference", {}).get("preferredAspirations", []))
    aspiration_score = 10 if aspiration_ok else 0
    score += aspiration_score
    section_scores["careerAspirationPreference"] = aspiration_score
    if not aspiration_ok:
        missing_sections.append("careerAspirationPreference")
        insights.append({
            "area": "careerAspirationPreference",
            "observation": "Career aspiration preferences missing",
            "action": "set_preferences",
            "recommendation": "Add preferred career aspirations"
        })

    location_pref = profile.get("careerLocationPreference", {})
    preferred_regions = location_pref.get("preferredRelocationRegions", [])
    relocation_timeline = location_pref.get("preferredRelocationTimeline", {})
    timeline_code = relocation_timeline.get("code", "") if isinstance(relocation_timeline, dict) else ""
    location_ok = has_items(preferred_regions) or (timeline_code == "NO")
    location_score = 10 if location_ok else 0
    score += location_score
    section_scores["careerLocationPreference"] = location_score
    if not location_ok:
        missing_sections.append("careerLocationPreference")
        insights.append({
            "area": "careerLocationPreference",
            "observation": "Relocation preferences missing",
            "action": "set_preferences",
            "recommendation": "Add preferred relocation regions or indicate relocation preference"
        })

    role_ok = has_items(profile.get("careerRolePreference", {}).get("preferredRoles", []))
    role_score = 10 if role_ok else 0
    score += role_score
    section_scores["careerRolePreference"] = role_score
    if not role_ok:
        missing_sections.append("careerRolePreference")
        insights.append({
            "area": "careerRolePreference",
            "observation": "Preferred roles missing",
            "action": "set_preferences",
            "recommendation": "Add preferred roles or role classifications"
        })

    lang_ok = has_items(profile.get("language", {}).get("languages", []))
    lang_score = 10 if lang_ok else 0
    score += lang_score
    section_scores["language"] = lang_score
    if not lang_ok:
        missing_sections.append("languages")
        insights.append({
            "area": "language",
            "observation": "No language proficiency data found",
            "action": "update_profile_field",
            "recommendation": "Add at least one language with proficiency level"
        })

    completion_score = round(score, 2)
    next_actions = []

    if completion_score < completion_threshold:
        for i, insight in enumerate(insights, start=1):
            next_actions.append({
                "title": insight["recommendation"],
                "tool": insight["action"],
                "priority": i
            })
    else:
        next_actions = [
            {"title": "Find Job Matches", "tool": "get_matches", "priority": 1},
            {"title": "Ask about a Job", "tool": "ask_jd_qa", "priority": 2}
        ]

    return {
        "success": True,
        "error": None,
        "completionScore": completion_score,
        "sectionScores": section_scores,
        "missingSections": missing_sections,
        "insights": insights,
        "nextActions": next_actions,
    }
