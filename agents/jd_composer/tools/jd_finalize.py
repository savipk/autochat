"""
JD Finalize tool -- Marks a JD draft as complete.
"""

from datetime import datetime

from langchain_core.tools import tool


@tool
def jd_finalize(draft_id: str) -> dict:
    """Finalizes a job description draft, marking it as ready for posting.
    Returns the complete finalized JD."""
    return run_jd_finalize(draft_id)


def run_jd_finalize(draft_id: str) -> dict:
    """Actual implementation -- returns mock finalized JD."""
    return {
        "success": True,
        "draft_id": draft_id,
        "status": "finalized",
        "finalized_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "jd_reference": f"JD-{datetime.now().strftime('%Y%m%d')}-001",
        "message": "Job description has been finalized and is ready for posting.",
        "next_steps": [
            "Submit for approval",
            "Post to internal job board",
            "Share with recruiting team",
        ],
    }
