"""
Get matches tool -- Functional implementation.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

from langchain_core.tools import tool

from core.profile import load_profile

logger = logging.getLogger("chatbot.tools")

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
    return run_get_matches(filters=filters, search_text=search_text, top_k=top_k)


def run_get_matches(
    filters: dict[str, Any] | None = None,
    search_text: str | None = None,
    top_k: int = DEFAULT_MATCH_TOP_K,
) -> dict[str, Any]:
    """Actual implementation -- loads profile from the configured data path."""
    if not isinstance(top_k, int) or top_k < 1:
        return {"success": False, "error": "top_k must be a positive integer."}

    _profile = load_profile()  # noqa: F841  -- will be used once real matching is added

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
            "averageScore": 0,
        }
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON in job data file: %s", e)
        return {
            "success": False,
            "error": "Job data file contains invalid JSON.",
            "matches": [],
            "count": 0,
            "averageScore": 0,
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
        "success": True,
        "error": None,
        "matches": matches,
        "count": len(matches),
        "averageScore": round(avg_score, 2),
        "filters_applied": filters or {},
        "search_text_used": search_text,
    }
