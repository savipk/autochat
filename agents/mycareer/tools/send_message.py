"""
Send message tool -- Mocked implementation.
Copied AS IS from tpchat/src/tools.py.
"""

from datetime import datetime

from langchain_core.tools import tool


@tool
def send_message(
    recipient_name: str,
    message_body: str,
    message_type: str = "teams",
    job_id: str | None = None,
) -> dict:
    """Sends a drafted message to the specified recipient via Teams or email."""
    return run_send_message(recipient_name, message_body, message_type, job_id)


def run_send_message(
    recipient_name: str,
    message_body: str,
    message_type: str = "teams",
    job_id: str | None = None,
) -> dict:
    """Actual implementation."""
    job_context = {
        "job_id": job_id or "331525BR",
        "job_title": "GenAI Lead",
        "level": "Executive Director",
        "location": "United States",
        "org_line": "GWM COO Americas"
    }

    return {
        "success": True,
        "recipient_name": recipient_name or "Prasanth Jagannathan",
        "message_type": message_type,
        "sent_at": datetime.now().strftime("%I:%M %p"),
        "job_context": job_context,
        "confirmation_message": f"Sent message to {recipient_name or 'Prasanth Jagannathan'}. View in Teams.",
        "suggest_apply": True
    }
