"""
Open profile panel tool -- triggers the profile side panel via SSE.
"""

from typing import Any

import chainlit as cl
from langchain_core.tools import tool

from core.profile_routes import push_panel_event


@tool
async def open_profile_panel() -> dict:
    """Opens the profile editor side panel for the user.
    Call this when the user wants to view, edit, review, or improve their profile."""
    return run_open_profile_panel()


def run_open_profile_panel() -> dict[str, Any]:
    """Actual implementation -- pushes an SSE event to open the panel."""
    try:
        user = cl.user_session.get("user")
        if user and hasattr(user, "metadata"):
            username = user.identifier
            push_panel_event(username, "open_panel")
            return {"success": True, "error": None}
        return {"success": False, "error": "Could not determine user context."}
    except Exception as e:
        return {"success": False, "error": str(e)}
