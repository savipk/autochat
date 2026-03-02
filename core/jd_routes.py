"""
FastAPI routes for the JD editor side panel.

Mounted on Chainlit's app as ``/api/jd/*``.
"""

import logging
from typing import Any

from fastapi import APIRouter, Header
from pydantic import BaseModel

from core.jd_manager import JDDraftManager

logger = logging.getLogger("chatbot.jd_routes")

router = APIRouter(prefix="/api/jd")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class JDDraftSaveRequest(BaseModel):
    jd_data: dict[str, Any]
    label: str = ""


class SectionUpdateRequest(BaseModel):
    section: str
    content: str
    label: str = ""


class JDSubmitRequest(BaseModel):
    """Empty body — finalize always acts on the latest draft."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _manager(username: str) -> JDDraftManager:
    return JDDraftManager(username=username)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/drafts")
async def list_drafts(x_username: str = Header(...)):
    """List all JD drafts for the user."""
    mgr = _manager(x_username)
    return mgr.list_drafts()


@router.post("/drafts")
async def save_draft(body: JDDraftSaveRequest, x_username: str = Header(...)):
    """Save a new JD draft snapshot."""
    mgr = _manager(x_username)
    draft_id = mgr.save_draft(body.jd_data, body.label)
    return {"draft_id": draft_id}


@router.get("/drafts/{draft_id}")
async def load_draft(draft_id: str, x_username: str = Header(...)):
    """Load a specific JD draft by id."""
    mgr = _manager(x_username)
    return mgr.load_draft(draft_id)


@router.get("/latest")
async def load_latest(x_username: str = Header(...)):
    """Load the most recent JD draft."""
    mgr = _manager(x_username)
    return mgr.load_latest()


@router.post("/drafts/{draft_id}/sections")
async def update_section(
    draft_id: str,
    body: SectionUpdateRequest,
    x_username: str = Header(...),
):
    """Update a section in the latest draft (creates a new version)."""
    mgr = _manager(x_username)
    new_id = mgr.update_section(body.section, body.content, body.label)
    return {"draft_id": new_id}


@router.post("/submit")
async def submit_jd(x_username: str = Header(...)):
    """Finalize the latest JD draft."""
    mgr = _manager(x_username)
    draft_id = mgr.finalize()
    if not draft_id:
        return {"success": False, "error": "No draft to finalize."}
    return {"success": True, "draft_id": draft_id}
