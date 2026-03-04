"""
Shared profile completion scoring.

Single source of truth for computing profile completion percentage.
Uses SECTION_REGISTRY weights from core.profile_schema.
"""

from __future__ import annotations

from typing import Any

from core.profile_schema import SECTION_REGISTRY

# Sections that may exist at root level in real profiles (e.g. miro_profile)
# but need to be under profile["core"] for scoring and updates.
_ROOT_SECTIONS = (
    "experience", "qualification", "skills",
    "careerAspirationPreference", "careerLocationPreference",
    "careerRolePreference", "language",
)


def normalize_profile(profile: dict[str, Any]) -> None:
    """Copy root-level sections into ``profile["core"]`` if missing there.

    Real HR profiles (e.g. miro_profile.json) store sections at the root
    level, not under ``core``.  The side panel's ``normalizeProfile()`` in
    ``custom.js`` already does this for rendering — this is the Python
    equivalent so scoring, updates, and adapter logic all see consistent data.

    Mutates *profile* in place.
    """
    core = profile.setdefault("core", {})
    for section in _ROOT_SECTIONS:
        if section not in core and profile.get(section) is not None:
            core[section] = profile[section]
    if "completionScore" not in core and "completionScore" in profile:
        core["completionScore"] = profile["completionScore"]


def compute_completion_score(profile: dict[str, Any]) -> int:
    """Compute profile completion as a weighted percentage (0–100).

    Always reads from ``profile["core"]`` to handle properly structured profiles.
    Normalizes root-level data into ``core`` first so that both layouts work.
    """
    normalize_profile(profile)
    core = profile.get("core", {})
    total_weight = 0
    earned_weight = 0

    for name, info in SECTION_REGISTRY.items():
        total_weight += info.weight
        section_data = core.get(info.storage_key)
        if not section_data:
            continue

        if name == "skills":
            if isinstance(section_data, dict):
                has_data = bool(section_data.get("top")) or bool(section_data.get("additional"))
            else:
                has_data = bool(section_data)
        elif name == "careerLocationPreference":
            # Location is valid if regions exist or timeline says NO relocation
            preferred_regions = section_data.get("preferredRelocationRegions", [])
            timeline = section_data.get("preferredRelocationTimeline", {})
            timeline_code = timeline.get("code", "") if isinstance(timeline, dict) else ""
            has_data = bool(preferred_regions) or timeline_code == "NO"
        elif info.list_field:
            items = section_data.get(info.list_field, [])
            has_data = isinstance(items, list) and len(items) > 0
        else:
            has_data = bool(section_data)

        if has_data:
            earned_weight += info.weight

    if total_weight == 0:
        return 0
    return round(earned_weight / total_weight * 100)


def compute_section_scores(profile: dict[str, Any]) -> dict[str, int]:
    """Return per-section scores (weight earned or 0)."""
    normalize_profile(profile)
    core = profile.get("core", {})
    scores: dict[str, int] = {}

    for name, info in SECTION_REGISTRY.items():
        section_data = core.get(info.storage_key)
        if not section_data:
            scores[info.storage_key] = 0
            continue

        if name == "skills":
            if isinstance(section_data, dict):
                has_data = bool(section_data.get("top")) or bool(section_data.get("additional"))
            else:
                has_data = bool(section_data)
        elif name == "careerLocationPreference":
            preferred_regions = section_data.get("preferredRelocationRegions", [])
            timeline = section_data.get("preferredRelocationTimeline", {})
            timeline_code = timeline.get("code", "") if isinstance(timeline, dict) else ""
            has_data = bool(preferred_regions) or timeline_code == "NO"
        elif info.list_field:
            items = section_data.get(info.list_field, [])
            has_data = isinstance(items, list) and len(items) > 0
        else:
            has_data = bool(section_data)

        scores[info.storage_key] = info.weight if has_data else 0

    return scores


def get_missing_sections(profile: dict[str, Any]) -> list[str]:
    """Return list of section storage keys that have no data."""
    scores = compute_section_scores(profile)
    return [key for key, score in scores.items() if score == 0]
