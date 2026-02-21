"""
Send message tool -- Mocked implementation.
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
    if not recipient_name or not isinstance(recipient_name, str):
        return {"success": False, "error": "recipient_name is required and must be a non-empty string."}

    if not message_body or not isinstance(message_body, str):
        return {"success": False, "error": "message_body is required and must be a non-empty string."}

    valid_types = ("teams", "email")
    if message_type not in valid_types:
        return {"success": False, "error": f"message_type must be one of {valid_types}."}

    job_context = {
        "job_id": job_id or "331525BR",
        "job_title": "GenAI Lead",
        "level": "Executive Director",
        "location": "United States",
        "org_line": "GWM COO Americas"
    }

    return {
        "success": True,
        "error": None,
        "recipient_name": recipient_name,
        "message_type": message_type,
        "sent_at": datetime.now().strftime("%I:%M %p"),
        "job_context": job_context,
        "confirmation_message": f"Sent message to {recipient_name}. View in Teams.",
        "suggest_apply": True
    }
