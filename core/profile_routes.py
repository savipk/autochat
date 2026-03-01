"""
FastAPI routes for the profile editor side panel.

Mounted on Chainlit's app as ``/api/profile/*``.
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.profile_manager import ProfileManager

logger = logging.getLogger("chatbot.profile_routes")

router = APIRouter(prefix="/api/profile")

# Tracks whether the profile was updated by the chat agent so the panel can poll.
# Maps username -> bool
_profile_updated_flags: dict[str, bool] = {}

# SSE queues — one per connected username
_sse_queues: dict[str, list[asyncio.Queue]] = {}


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
# SSE endpoint — pushes panel events to the browser
# ---------------------------------------------------------------------------

@router.get("/events")
async def profile_events(username: str = Query(...)):
    """SSE stream that pushes panel open/refresh events to the browser.

    Uses a query parameter (not a header) so the browser-native EventSource
    API can connect without custom headers.
    """
    queue: asyncio.Queue = asyncio.Queue()
    _sse_queues.setdefault(username, []).append(queue)

    async def _generator():
        try:
            yield ": connected\n\n"
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            queues = _sse_queues.get(username, [])
            if queue in queues:
                queues.remove(queue)

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# /whoami — returns username + profile_path for the logged-in user
# ---------------------------------------------------------------------------

# Populated by app.py on login so we can look up user metadata here.
_user_metadata: dict[str, dict[str, str]] = {}


def register_user_metadata(username: str, profile_path: str):
    """Called from app.py to store the mapping for /whoami lookups."""
    _user_metadata[username] = {"username": username, "profile_path": profile_path}


@router.get("/whoami")
async def whoami(x_username: str = Header(...)):
    """Return user context needed by the side panel JS."""
    meta = _user_metadata.get(x_username, {})
    return meta or {"username": x_username, "profile_path": ""}


# ---------------------------------------------------------------------------
# Helpers used by app.py action callbacks
# ---------------------------------------------------------------------------

def push_panel_event(username: str, event_type: str = "open_panel"):
    """Push an SSE event to all connected clients for this user."""
    queues = _sse_queues.get(username, [])
    logger.debug("push_panel_event: username=%s event=%s queues=%d",
                 username, event_type, len(queues))
    for q in queues:
        q.put_nowait({"type": event_type})


def set_profile_updated(username: str):
    """Signal that the profile was updated (called after approve action)."""
    _profile_updated_flags[username] = True
    push_panel_event(username, "refresh")


def _clear_middleware_cache():
    """Clear the mycareer middleware thread analysis cache."""
    try:
        from agents.mycareer.middleware import clear_profile_cache
        clear_profile_cache()
    except ImportError:
        logger.debug("Could not import clear_profile_cache")
