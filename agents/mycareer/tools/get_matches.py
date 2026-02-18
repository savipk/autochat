"""
Get matches tool -- Functional implementation.
Copied AS IS from tpchat/src/tools.py.
"""

import json
import os
from datetime import datetime
from typing import Any

from langchain_core.tools import tool

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "matching_jobs.json")
DEFAULT_MATCH_TOP_K = 3


@tool
def get_matches(
    filters: dict | None = None,
    search_text: str | None = None,
    top_k: int = DEFAULT_MATCH_TOP_K,
) -> dict:
    """Finds and returns the top matching internal job postings that best fit
    the user's profile and preferences."""
    return run_get_matches({}, filters=filters, search_text=search_text, top_k=top_k)


def run_get_matches(
    profile: dict[str, Any],
    filters: dict[str, Any] | None = None,
    search_text: str | None = None,
    top_k: int = DEFAULT_MATCH_TOP_K,
) -> dict[str, Any]:
    """Actual implementation."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        return {
            "matches": [],
            "count": 0,
            "averageScore": 0,
            "message": f"Error loading job data: {e}",
            "success": False
        }

    jobs = data.get("jobs", [])
    today = datetime.now().date()

    matches = []
    for job in jobs[:top_k]:
        posted_date_str = job.get("postedDate", "")
        days_ago = None
        is_new = False

        if posted_date_str:
            try:
                posted_date = datetime.fromisoformat(posted_date_str).date()
                days_ago = (today - posted_date).days
                is_new = days_ago <= 7
            except ValueError:
                pass

        matches.append({
            **job,
            "daysAgo": days_ago,
            "isNew": is_new,
        })

    avg_score = sum(m.get("matchScore", 0) for m in matches) / len(matches) if matches else 0

    return {
        "matches": matches,
        "count": len(matches),
        "averageScore": round(avg_score, 2),
        "filters_applied": filters or {},
        "search_text_used": search_text,
        "success": True
    }
