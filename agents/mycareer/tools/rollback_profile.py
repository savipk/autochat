"""
Rollback profile tool -- restores the user's profile from the most recent backup.
"""

from __future__ import annotations

from typing import Any

import chainlit as cl
from langchain_core.tools import tool

from core.profile_manager import ProfileManager
from core.profile_score import compute_completion_score


def _get_user_context() -> tuple[str, str]:
    """Extract username and profile_path from the Chainlit session."""
    try:
        user = cl.user_session.get("user")
        if user and hasattr(user, "metadata") and user.metadata:
            return user.identifier, user.metadata.get("profile_path", "")
    except Exception:
        pass
    return "", ""


@tool
def rollback_profile() -> dict:
    """Rolls back the user's profile to the most recent backup.

    Use this when the user wants to undo a recent profile change.
    """
    return run_rollback_profile()


def run_rollback_profile() -> dict[str, Any]:
    """Restore profile from backup."""
    username, profile_path = _get_user_context()
    if not username or not profile_path:
        return {
            "success": False,
            "error": "Cannot rollback: missing username or profile_path in session.",
        }

    mgr = ProfileManager(username=username, profile_path=profile_path)
    restored = mgr.rollback()

    if restored is None:
        return {
            "success": False,
            "error": "No backups available to rollback to.",
        }

    new_score = compute_completion_score(restored)

    return {
        "success": True,
        "error": None,
        "message": "Profile restored from most recent backup.",
        "completion_score": new_score,
    }
