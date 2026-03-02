"""
View job tool -- returns job details for a specific role.

The SSE event to open the JD panel is pushed by app.py post-orchestrator
(same pattern as open_profile_panel).
"""

import json
import os
from typing import Any

from langchain_core.tools import tool


@tool
async def view_job(job_id: str) -> dict:
    """Opens the job description panel for a specific role.
    Always confirm the job ID with the user first before calling this tool."""
    return run_view_job(job_id)


def run_view_job(job_id: str) -> dict[str, Any]:
    """Load job data by ID and return it. SSE push is handled by app.py."""
    try:
        jobs_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "matching_jobs.json")
        jobs_path = os.path.normpath(jobs_path)

        with open(jobs_path, "r") as f:
            data = json.load(f)

        jobs = data.get("jobs", [])
        job = next((j for j in jobs if j.get("id") == job_id), None)

        if not job:
            return {"success": False, "error": f"Job ID '{job_id}' not found."}

        return {"success": True, "job_id": job_id, "job": job}
    except Exception as e:
        return {"success": False, "error": str(e)}
