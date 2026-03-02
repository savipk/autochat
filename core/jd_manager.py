"""
JD Draft Manager -- CRUD operations with immutable draft versioning.

Mirrors the ProfileManager pattern but for JD drafts. Each save/update
creates a new timestamped snapshot so users can navigate version history.
"""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger("chatbot.jd_manager")

JD_DRAFTS_BASE_DIR = "data/jd_drafts"


class JDDraftManager:
    """Per-user JD draft operations: save, list, load, update section, finalize."""

    def __init__(self, username: str):
        self.username = username
        self._drafts_dir = os.path.join(JD_DRAFTS_BASE_DIR, username)

    def save_draft(self, jd_data: dict, label: str = "") -> str:
        """Create a timestamped draft snapshot. Returns the draft_id."""
        os.makedirs(self._drafts_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        draft_id = f"jd_draft_{ts}"
        draft_path = os.path.join(self._drafts_dir, f"{draft_id}.json")

        payload = dict(jd_data)
        payload["_meta"] = {
            "draft_id": draft_id,
            "timestamp": ts,
            "label": label,
            "finalized": False,
        }

        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        logger.info("JD draft saved: %s", draft_path)
        return draft_id

    def list_drafts(self) -> list[dict]:
        """Return ``[{id, timestamp, label, finalized}]`` sorted oldest-first."""
        if not os.path.isdir(self._drafts_dir):
            return []

        drafts = []
        for fname in sorted(os.listdir(self._drafts_dir)):
            if not fname.startswith("jd_draft_") or not fname.endswith(".json"):
                continue
            fpath = os.path.join(self._drafts_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = data.get("_meta", {})
                drafts.append({
                    "id": meta.get("draft_id", fname.replace(".json", "")),
                    "timestamp": meta.get("timestamp", ""),
                    "label": meta.get("label", ""),
                    "finalized": meta.get("finalized", False),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return drafts

    def load_draft(self, draft_id: str) -> dict:
        """Read a specific draft by id."""
        draft_path = os.path.join(self._drafts_dir, f"{draft_id}.json")
        try:
            with open(draft_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load JD draft %s: %s", draft_id, e)
            return {}

    def load_latest(self) -> dict:
        """Load the most recent draft (by filename sort order)."""
        drafts = self.list_drafts()
        if not drafts:
            return {}
        return self.load_draft(drafts[-1]["id"])

    def update_section(self, section: str, content: str, label: str = "") -> str:
        """Update a section in the latest draft and save as a new version.

        Creates a new immutable snapshot with the section replaced.
        Returns the new draft_id.
        """
        latest = self.load_latest()
        if not latest:
            logger.warning("No existing draft to update section '%s'", section)
            return ""

        sections = latest.get("sections", {})
        sections[section] = content
        latest["sections"] = sections

        # Strip old _meta before saving (save_draft adds fresh _meta)
        latest.pop("_meta", None)

        return self.save_draft(latest, label=label or f"Updated {section}")

    def finalize(self) -> str:
        """Mark the latest draft as finalized. Returns the draft_id."""
        latest = self.load_latest()
        if not latest:
            logger.warning("No draft to finalize")
            return ""

        latest.pop("_meta", None)

        os.makedirs(self._drafts_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        draft_id = f"jd_draft_{ts}"
        draft_path = os.path.join(self._drafts_dir, f"{draft_id}.json")

        latest["_meta"] = {
            "draft_id": draft_id,
            "timestamp": ts,
            "label": "Finalized",
            "finalized": True,
        }

        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(latest, f, indent=2)

        logger.info("JD draft finalized: %s", draft_path)
        return draft_id
