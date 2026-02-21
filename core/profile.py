"""
Shared profile loader.

All tools and middleware that need user-profile data should import
``load_profile`` from here rather than passing the profile through
runtime context.
"""

import json
import logging
import os

from core.config import PROFILE_PATH

logger = logging.getLogger("chatbot.profile")


def load_profile(path: str | None = None) -> dict:
    """Load the user profile JSON from disk.

    Uses the ``PROFILE_PATH`` configuration value by default.  An
    explicit *path* can be supplied for tests or one-off overrides.
    """
    profile_path = path or PROFILE_PATH
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Profile file not found: %s", profile_path)
        return {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load profile from %s: %s", profile_path, e)
        return {}


def user_name_from_profile(profile: dict | None = None) -> str:
    """Extract a display name from a profile dict.

    If *profile* is ``None``, loads from the default path.
    """
    if profile is None:
        profile = load_profile()
    core = profile.get("core", {})
    name_info = core.get("name", {})
    return (
        f"{name_info.get('businessFirstName', '')} "
        f"{name_info.get('businessLastName', '')}"
    ).strip()
