"""
FastAPI routes for the profile editor side panel.

Mounted on Chainlit's app as ``/api/profile/*``.
"""

import logging
from typing import Any

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from core.profile_manager import ProfileManager

logger = logging.getLogger("chatbot.profile_routes")

router = APIRouter(prefix="/api/profile")

# Tracks whether the profile was updated by the chat agent so the panel can poll.
# Maps username -> bool
_profile_updated_flags: dict[str, bool] = {}


def _manager(username: str, profile_path: str) -> ProfileManager:
    return ProfileManager(username=username, profile_path=profile_path)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class DraftSaveRequest(BaseModel):
    profile_data: dict[str, Any]
    label: str = ""


class SubmitRequest(BaseModel):
    profile_data: dict[str, Any]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/current")
async def get_current_profile(
    x_username: str = Header(...),
    x_profile_path: str = Header(...),
):
    """Return the full committed profile JSON."""
    mgr = _manager(x_username, x_profile_path)
    return mgr.load_current()


@router.get("/drafts")
async def list_drafts(
    x_username: str = Header(...),
    x_profile_path: str = Header(...),
):
    """List all saved drafts for the user."""
    mgr = _manager(x_username, x_profile_path)
    return mgr.list_drafts()


@router.post("/drafts")
async def save_draft(
    body: DraftSaveRequest,
    x_username: str = Header(...),
    x_profile_path: str = Header(...),
):
    """Save a new draft snapshot."""
    mgr = _manager(x_username, x_profile_path)
    draft_id = mgr.save_draft(body.profile_data, body.label)
    return {"draft_id": draft_id}


@router.get("/drafts/{draft_id}")
async def load_draft(
    draft_id: str,
    x_username: str = Header(...),
    x_profile_path: str = Header(...),
):
    """Load a specific draft by id."""
    mgr = _manager(x_username, x_profile_path)
    return mgr.load_draft(draft_id)


@router.post("/submit")
async def submit_profile(
    body: SubmitRequest,
    x_username: str = Header(...),
    x_profile_path: str = Header(...),
):
    """Persist profile to disk and clear middleware cache."""
    mgr = _manager(x_username, x_profile_path)
    mgr.submit(body.profile_data)

    # Clear middleware analysis cache so agent sees fresh data
    _clear_middleware_cache()

    return {"success": True}


@router.get("/poll-update")
async def poll_update(x_username: str = Header(...)):
    """Check if the chat agent updated the profile. Clears flag on read."""
    updated = _profile_updated_flags.pop(x_username, False)
    return {"updated": updated}


# ---------------------------------------------------------------------------
# Helpers used by app.py action callbacks
# ---------------------------------------------------------------------------

def set_profile_updated(username: str):
    """Signal that the profile was updated (called after approve action)."""
    _profile_updated_flags[username] = True


def _clear_middleware_cache():
    """Clear the mycareer middleware thread analysis cache."""
    try:
        from agents.mycareer.middleware import clear_profile_cache
        clear_profile_cache()
    except ImportError:
        logger.debug("Could not import clear_profile_cache")
