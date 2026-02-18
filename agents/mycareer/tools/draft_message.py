"""
Draft message tool -- Mocked implementation.
Copied AS IS from tpchat/src/tools.py.
"""

from typing import Any

from langchain_core.tools import tool


@tool
def draft_message(
    job_id: str | None = None,
    recipient_type: str = "hiring_manager",
    recipient_name: str | None = None,
    purpose: str | None = None,
    tone: str = "formal",
) -> dict:
    """Drafts a Teams message to a hiring manager or recruiter for a
    specific job posting or internal contact."""
    raise RuntimeError("draft_message requires a profile; use run_draft_message instead")


def run_draft_message(
    profile: dict[str, Any],
    job_id: str | None = None,
    recipient_type: str = "hiring_manager",
    recipient_name: str | None = None,
    purpose: str | None = None,
    tone: str = "formal",
) -> dict[str, Any]:
    """Actual implementation."""
    core = profile.get("core", {})
    name = core.get("name", {})
    user_first_name = name.get("businessFirstName", "")
    user_last_name = name.get("businessLastName", "")
    user_name = f"{user_first_name} {user_last_name}".strip() or "Candidate"

    recipient = recipient_name or "Prasanth Jagannathan"
    job_title = "GenAI Lead"

    recipient_first = recipient.split()[0] if recipient else "there"
    message_body = (
        f"Hi {recipient_first}, I'm {user_first_name or 'interested'} and I'm interested "
        f"in the **{job_title}** role. Could you share a bit more about the project this "
        f"role will lead?\n\nHappy to meet for a quick coffee chat too. You can also view "
        f"my profile in MyCareer for more context.\n\nLooking forward to your reply. Thank you!"
    )

    return {
        "recipient_name": recipient,
        "sender_name": user_name,
        "sender_first_name": user_first_name or user_name.split()[0],
        "job_title": job_title,
        "job_id": job_id or "331525BR",
        "message_body": message_body,
        "message_type": "teams",
        "purpose": purpose or "express interest",
        "success": True,
        "can_edit": True,
        "profile_link": True
    }
