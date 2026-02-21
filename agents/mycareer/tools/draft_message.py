"""
Draft message tool -- Mocked implementation.
"""

from typing import Any

from langchain_core.tools import tool

from core.profile import load_profile


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
    return run_draft_message(
        job_id=job_id, recipient_type=recipient_type,
        recipient_name=recipient_name, purpose=purpose, tone=tone,
    )


def run_draft_message(
    job_id: str | None = None,
    recipient_type: str = "hiring_manager",
    recipient_name: str | None = None,
    purpose: str | None = None,
    tone: str = "formal",
) -> dict[str, Any]:
    """Actual implementation -- loads profile from the configured data path."""
    valid_tones = ("formal", "casual", "friendly")
    if tone not in valid_tones:
        return {"success": False, "error": f"tone must be one of {valid_tones}."}

    valid_recipient_types = ("hiring_manager", "recruiter", "contact")
    if recipient_type not in valid_recipient_types:
        return {"success": False, "error": f"recipient_type must be one of {valid_recipient_types}."}

    profile = load_profile()
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
        "success": True,
        "error": None,
        "recipient_name": recipient,
        "sender_name": user_name,
        "sender_first_name": user_first_name or user_name.split()[0],
        "job_title": job_title,
        "job_id": job_id or "331525BR",
        "message_body": message_body,
        "message_type": "teams",
        "purpose": purpose or "express interest",
        "can_edit": True,
        "profile_link": True
    }
