"""
Get matches tool -- Functional implementation.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

from langchain_core.tools import tool

from core.profile import load_profile

logger = logging.getLogger("chatbot.tools")

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "matching_jobs.json")
DEFAULT_MATCH_TOP_K = 3

# Session-level tracking of seen job IDs, keyed by thread_id.
_seen_jobs: dict[str, set[str]] = {}


def _reset_seen_jobs() -> None:
    """Clear all seen-job tracking (for tests)."""
    _seen_jobs.clear()


def _match_filter(job: dict, key: str, value: Any, today: datetime) -> bool:
    """Return True if *job* passes a single filter criterion."""
    val_lower = str(value).lower() if isinstance(value, str) else value

    if key == "country":
        return val_lower in job.get("country", "").lower()
    if key == "location":
        return val_lower in job.get("location", "").lower()
    if key == "corporateTitle":
        return val_lower in job.get("corporateTitle", "").lower()
    if key == "level":
        return job.get("corporateTitleCode", "").upper() == str(value).upper()
    if key in ("orgLine", "department"):
        return val_lower in job.get("orgLine", "").lower()
    if key == "skills":
        if isinstance(value, list):
            job_skills = {s.lower() for s in job.get("matchingSkills", [])}
            return any(s.lower() in job_skills for s in value)
        return False
    if key == "minScore":
        try:
            return job.get("matchScore", 0) >= float(value)
        except (TypeError, ValueError):
            return True
    if key == "postedWithin":
        try:
            days = int(value)
        except (TypeError, ValueError):
            return True
        posted = job.get("postedDate", "")
        if not posted:
            return False
        try:
            posted_date = datetime.fromisoformat(posted).date()
            return (today.date() - posted_date).days <= days
        except ValueError:
            return False

    # Unknown filter keys are ignored gracefully
    return True


def _match_search(job: dict, search_text: str) -> bool:
    """Return True if all terms in *search_text* appear somewhere in the job."""
    terms = search_text.lower().split()
    if not terms:
        return True

    searchable_fields = [
        job.get("title", ""),
        job.get("summary", ""),
        job.get("yourRole", ""),
        job.get("orgLine", ""),
        job.get("location", ""),
    ]
    # Include requirements list
    reqs = job.get("requirements", [])
    if isinstance(reqs, list):
        searchable_fields.extend(reqs)

    combined = " ".join(searchable_fields).lower()
    return all(term in combined for term in terms)


def _build_profile_summary(profile: dict) -> dict[str, Any]:
    """Extract a lightweight profile summary for the response."""
    core = profile.get("core", {})
    name_data = core.get("name", {})
    first = name_data.get("businessFirstName", "")
    last = name_data.get("businessLastName", "")
    name = f"{first} {last}".strip() or "User"

    skills_data = core.get("skills", {})
    top_skills: list[str] = []
    if isinstance(skills_data, dict):
        for s in skills_data.get("top", []):
            if isinstance(s, dict):
                top_skills.append(s.get("name", ""))
            else:
                top_skills.append(str(s))
        for s in skills_data.get("additional", []):
            if isinstance(s, dict):
                top_skills.append(s.get("name", ""))
            else:
                top_skills.append(str(s))

    # Compute a simple completion score (percentage of key sections present)
    sections = ["experience", "qualification", "skills", "careerAspirationPreference",
                 "careerLocationPreference", "careerRolePreference", "language"]
    filled = sum(1 for s in sections if core.get(s))
    completion_score = round(filled / len(sections) * 100)

    return {
        "name": name,
        "topSkills": top_skills[:5],
        "completionScore": completion_score,
    }


@tool
def get_matches(
    filters: dict | None = None,
    search_text: str | None = None,
    top_k: int = DEFAULT_MATCH_TOP_K,
    offset: int = 0,
) -> dict:
    """Finds and returns the top matching internal job postings that best fit
    the user's profile and preferences.

    Args:
        filters: Optional dict of filter criteria. Supported keys:
            - country: case-insensitive substring match on job country
            - location: case-insensitive substring match on job location
            - corporateTitle: case-insensitive substring match on corporate title
            - level: case-insensitive exact match on corporateTitleCode (AS, AO, AD, DIR, ED, MD)
            - orgLine / department: case-insensitive substring match on orgLine
            - skills: list of skill names — matches if any overlap with job's matchingSkills
            - minScore: minimum matchScore threshold (e.g. 2.0)
            - postedWithin: number of days — only jobs posted within N days
        search_text: Optional natural language search. All words must appear
            (AND logic) across title, summary, yourRole, orgLine, location,
            and requirements. E.g. "senior data engineering London".
        top_k: Maximum number of results to return (default 3).
        offset: Number of results to skip for pagination (default 0).

    Returns:
        Dict with matches, count, total_available, offset, has_more,
        profile_summary, and metadata about applied filters.
    """
    return run_get_matches(filters=filters, search_text=search_text,
                           top_k=top_k, offset=offset)


def run_get_matches(
    filters: dict[str, Any] | None = None,
    search_text: str | None = None,
    top_k: int = DEFAULT_MATCH_TOP_K,
    offset: int = 0,
    thread_id: str = "default",
) -> dict[str, Any]:
    """Actual implementation -- loads profile from the configured data path."""
    if not isinstance(top_k, int) or top_k < 1:
        return {"success": False, "error": "top_k must be a positive integer."}
    if not isinstance(offset, int) or offset < 0:
        offset = 0

    profile = load_profile()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning("Job data file not found: %s", DATA_FILE)
        return {
            "success": False,
            "error": f"Job data file not found at {DATA_FILE}",
            "matches": [],
            "count": 0,
            "total_available": 0,
            "offset": offset,
            "has_more": False,
            "averageScore": 0,
        }
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON in job data file: %s", e)
        return {
            "success": False,
            "error": "Job data file contains invalid JSON.",
            "matches": [],
            "count": 0,
            "total_available": 0,
            "offset": offset,
            "has_more": False,
            "averageScore": 0,
        }

    jobs = data.get("jobs", [])
    today = datetime.now()

    # --- Filtering ---
    if filters:
        filtered = []
        for job in jobs:
            if all(_match_filter(job, k, v, today) for k, v in filters.items()):
                filtered.append(job)
        jobs = filtered

    # --- Search ---
    if search_text and search_text.strip():
        jobs = [j for j in jobs if _match_search(j, search_text.strip())]

    # --- Sort by matchScore descending ---
    jobs.sort(key=lambda j: j.get("matchScore", 0), reverse=True)

    total_available = len(jobs)

    # --- Pagination ---
    paginated = jobs[offset: offset + top_k]

    has_more = (offset + top_k) < total_available

    # --- Seen-job tracking ---
    seen = _seen_jobs.setdefault(thread_id, set())

    matches = []
    for job in paginated:
        posted_date_str = job.get("postedDate", "")
        days_ago = None
        is_new = False

        if posted_date_str:
            try:
                posted_date = datetime.fromisoformat(posted_date_str).date()
                days_ago = (today.date() - posted_date).days
                is_new = days_ago <= 7
            except ValueError:
                pass

        job_id = job.get("id", "")
        is_new_to_user = job_id not in seen

        matches.append({
            **job,
            "daysAgo": days_ago,
            "isNew": is_new,
            "isNewToUser": is_new_to_user,
        })

    # Record all returned job IDs as seen
    for m in matches:
        seen.add(m.get("id", ""))

    avg_score = sum(m.get("matchScore", 0) for m in matches) / len(matches) if matches else 0

    profile_summary = _build_profile_summary(profile)

    return {
        "success": True,
        "error": None,
        "matches": matches,
        "count": len(matches),
        "total_available": total_available,
        "offset": offset,
        "has_more": has_more,
        "averageScore": round(avg_score, 2),
        "filters_applied": filters or {},
        "search_text_used": search_text,
        "profile_summary": profile_summary,
    }
