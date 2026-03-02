"""
View job tool -- opens the JD side panel for a specific role via SSE.
"""

import json
import os
from typing import Any

import chainlit as cl
from langchain_core.tools import tool

from core.profile_routes import push_panel_event


@tool
async def view_job(job_id: str) -> dict:
    """Opens the job description panel for a specific role.
    Always confirm the job ID with the user first before calling this tool."""
    return run_view_job(job_id)


def run_view_job(job_id: str) -> dict[str, Any]:
    """Load job data by ID and push an SSE event to open the JD panel."""
    try:
        # Load matching jobs
        jobs_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "matching_jobs.json")
        jobs_path = os.path.normpath(jobs_path)

        with open(jobs_path, "r") as f:
            data = json.load(f)

        jobs = data.get("jobs", [])
        job = next((j for j in jobs if j.get("id") == job_id), None)

        if not job:
            return {"success": False, "error": f"Job ID '{job_id}' not found."}

        # Push SSE event to open the JD panel
        user = cl.user_session.get("user")
        if user and hasattr(user, "metadata"):
            username = user.identifier
            push_panel_event(username, "open_jd_panel", data={"job_id": job_id})

        return {"success": True, "job_id": job_id, "title": job.get("title", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}
