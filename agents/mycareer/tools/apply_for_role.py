"""
Apply for role tool -- Mocked implementation.
Copied AS IS from tpchat/src/tools.py.
"""

from datetime import datetime
from typing import Any

from langchain_core.tools import tool


@tool
def apply_for_role(job_id: str, cover_letter: str | None = None) -> dict:
    """Submits an application for a specific job posting using the user's profile."""
    return run_apply_for_role(job_id, {}, cover_letter)


def run_apply_for_role(
    job_id: str,
    profile: dict[str, Any],
    cover_letter: str | None = None,
) -> dict[str, Any]:
    """Actual implementation."""
    job_details = {
        "job_id": job_id or "331525BR",
        "job_title": "GenAI Lead",
        "org_line": "GWM COO Americas",
        "location": "United States",
        "level": "Executive Director"
    }

    return {
        "success": True,
        "application_id": f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "job_id": job_details["job_id"],
        "job_title": job_details["job_title"],
        "org_line": job_details["org_line"],
        "applied_at": datetime.now().strftime("%I:%M %p"),
        "status": "submitted",
        "confirmation_message": f"Applied to '{job_details['job_title']}'. View application in goto/jobs.",
        "email_confirmation": True
    }
