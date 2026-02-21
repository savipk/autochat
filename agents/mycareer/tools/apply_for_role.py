"""
Apply for role tool -- Mocked implementation.
"""

from datetime import datetime
from typing import Any

from langchain_core.tools import tool

from core.profile import load_profile


@tool
def apply_for_role(job_id: str, cover_letter: str | None = None) -> dict:
    """Submits an application for a specific job posting using the user's profile."""
    return run_apply_for_role(job_id=job_id, cover_letter=cover_letter)


def run_apply_for_role(
    job_id: str = "",
    cover_letter: str | None = None,
) -> dict[str, Any]:
    """Actual implementation -- loads profile from the configured data path."""
    if not job_id or not isinstance(job_id, str):
        return {"success": False, "error": "job_id is required and must be a non-empty string."}

    _profile = load_profile()  # noqa: F841  -- will be used once real application logic is added

    job_details = {
        "job_id": job_id,
        "job_title": "GenAI Lead",
        "org_line": "GWM COO Americas",
        "location": "United States",
        "level": "Executive Director"
    }

    return {
        "success": True,
        "error": None,
        "application_id": f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "job_id": job_details["job_id"],
        "job_title": job_details["job_title"],
        "org_line": job_details["org_line"],
        "applied_at": datetime.now().strftime("%I:%M %p"),
        "status": "submitted",
        "confirmation_message": f"Applied to '{job_details['job_title']}'. View application in goto/jobs.",
        "email_confirmation": True
    }
