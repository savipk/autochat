"""
Profile manager -- CRUD operations with draft versioning and submit.

Handles loading/saving the user profile, creating timestamped draft
snapshots, and submitting (persisting) profile changes to disk.
Includes file locking, timestamped backup rotation, and rollback support.
"""

import fcntl
import json
import logging
import os
import shutil
from datetime import datetime, timezone

logger = logging.getLogger("chatbot.profile_manager")

DRAFTS_BASE_DIR = "data/drafts"
MAX_BACKUPS = 5


class ProfileManager:
    """Per-user profile operations: load, save drafts, submit, rollback."""

    def __init__(self, username: str, profile_path: str):
        self.username = username
        self.profile_path = profile_path
        self._drafts_dir = os.path.join(DRAFTS_BASE_DIR, username)
        self._backups_dir = os.path.join(
            os.path.dirname(profile_path), ".backups", username
        )

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

    def _create_timestamped_backup(self) -> str | None:
        """Create a timestamped backup of the current profile. Returns backup path."""
        if not os.path.exists(self.profile_path):
            return None

        os.makedirs(self._backups_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_path = os.path.join(self._backups_dir, f"profile_{ts}.json")
        shutil.copy2(self.profile_path, backup_path)
        logger.info("Backup created: %s", backup_path)

        # Prune old backups — keep only the most recent MAX_BACKUPS
        self._prune_backups()

        # Also maintain legacy .bak for backward compatibility
        bak_path = self.profile_path + ".bak"
        shutil.copy2(self.profile_path, bak_path)

        return backup_path

    def _prune_backups(self):
        """Remove old backups beyond MAX_BACKUPS (keep newest)."""
        if not os.path.isdir(self._backups_dir):
            return

        backups = sorted(
            [
                f
                for f in os.listdir(self._backups_dir)
                if f.startswith("profile_") and f.endswith(".json")
            ]
        )
        while len(backups) > MAX_BACKUPS:
            oldest = backups.pop(0)
            oldest_path = os.path.join(self._backups_dir, oldest)
            try:
                os.remove(oldest_path)
                logger.info("Pruned old backup: %s", oldest_path)
            except OSError as e:
                logger.warning("Failed to prune backup %s: %s", oldest_path, e)

    def list_backups(self) -> list[str]:
        """Return list of backup filenames sorted oldest-first."""
        if not os.path.isdir(self._backups_dir):
            return []
        return sorted(
            f
            for f in os.listdir(self._backups_dir)
            if f.startswith("profile_") and f.endswith(".json")
        )

    def get_latest_backup(self) -> dict | None:
        """Return the most recent backup profile dict without restoring it."""
        backups = self.list_backups()
        if not backups:
            return None
        latest = backups[-1]
        backup_path = os.path.join(self._backups_dir, latest)
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read backup %s: %s", backup_path, e)
            return None

    def submit(self, profile_data: dict) -> bool:
        """Persist profile to disk with file locking. Backs up current file first.

        Strips the internal ``_meta`` key before writing.
        Uses ``fcntl.flock`` for exclusive locking to prevent concurrent write corruption.
        """
        # Create timestamped backup
        self._create_timestamped_backup()

        # Strip _meta
        clean = {k: v for k, v in profile_data.items() if k != "_meta"}

        # Recalculate completion score before persisting
        from core.profile_score import compute_completion_score
        clean["completionScore"] = compute_completion_score(clean)

        # Write with exclusive file lock
        with open(self.profile_path, "w", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(clean, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        logger.info("Profile submitted: %s", self.profile_path)
        return True

    def rollback(self) -> dict | None:
        """Restore profile from the most recent backup.

        Returns the restored profile dict, or None if no backup exists.
        """
        backups = self.list_backups()
        if not backups:
            logger.warning("No backups found for rollback")
            return None

        latest = backups[-1]
        backup_path = os.path.join(self._backups_dir, latest)

        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to read backup %s: %s", backup_path, e)
            return None

        # Recalculate completion score for the restored profile
        from core.profile_score import compute_completion_score
        backup_data["completionScore"] = compute_completion_score(backup_data)

        # Write backup data as current profile (with locking)
        with open(self.profile_path, "w", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(backup_data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        logger.info("Profile rolled back from %s", backup_path)
        return backup_data
