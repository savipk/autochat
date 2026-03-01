"""
Profile manager -- CRUD operations with draft versioning and submit.

Handles loading/saving the user profile, creating timestamped draft
snapshots, and submitting (persisting) profile changes to disk.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timezone

logger = logging.getLogger("chatbot.profile_manager")

DRAFTS_BASE_DIR = "data/drafts"


class ProfileManager:
    """Per-user profile operations: load, save drafts, submit."""

    def __init__(self, username: str, profile_path: str):
        self.username = username
        self.profile_path = profile_path
        self._drafts_dir = os.path.join(DRAFTS_BASE_DIR, username)

    def load_current(self) -> dict:
        """Read the committed profile JSON from disk."""
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load profile %s: %s", self.profile_path, e)
            return {}

    def save_draft(self, profile_data: dict, label: str = "") -> str:
        """Create a timestamped draft snapshot. Returns the draft_id."""
        os.makedirs(self._drafts_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        draft_id = f"draft_{ts}"
        draft_path = os.path.join(self._drafts_dir, f"{draft_id}.json")

        payload = dict(profile_data)
        payload["_meta"] = {
            "draft_id": draft_id,
            "timestamp": ts,
            "label": label,
        }

        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        logger.info("Draft saved: %s", draft_path)
        return draft_id

    def list_drafts(self) -> list[dict]:
        """Return ``[{id, timestamp, label}]`` sorted oldest-first."""
        if not os.path.isdir(self._drafts_dir):
            return []

        drafts = []
        for fname in sorted(os.listdir(self._drafts_dir)):
            if not fname.startswith("draft_") or not fname.endswith(".json"):
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
            logger.warning("Failed to load draft %s: %s", draft_id, e)
            return {}

    def submit(self, profile_data: dict) -> bool:
        """Persist profile to disk. Backs up current file first.

        Strips the internal ``_meta`` key before writing.
        """
        # Back up current profile
        if os.path.exists(self.profile_path):
            bak_path = self.profile_path + ".bak"
            shutil.copy2(self.profile_path, bak_path)
            logger.info("Backed up profile to %s", bak_path)

        # Strip _meta
        clean = {k: v for k, v in profile_data.items() if k != "_meta"}

        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2)

        logger.info("Profile submitted: %s", self.profile_path)
        return True
