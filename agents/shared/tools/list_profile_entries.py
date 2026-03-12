"""
List profile entries tool -- returns entries in a section with their IDs.

Allows the agent to discover entry IDs for edit_entry/remove_entry operations
so the user never has to know or supply internal UUIDs.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from core.profile import load_profile
from core.profile_score import normalize_profile
from core.profile_schema import resolve_section, get_valid_section_names

ALLOWED_LIST_SECTIONS = {"experience"}


def _summarize_entry(section_name: str, entry: dict) -> str:
    """Build a human-readable one-line summary of a profile entry."""
    if section_name == "experience":
        title = entry.get("jobTitle", "Untitled")
        company = entry.get("company", "")
        start = entry.get("startDate", "")
        parts = [title]
        if company:
            parts.append(f"at {company}")
        if start:
            parts.append(f"({start})")
        return " ".join(parts)

    if section_name == "education":
        inst = entry.get("institutionName", "Unknown Institution")
        degree = entry.get("degree", "")
        parts = [inst]
        if degree:
            parts.append(f"- {degree}")
        return " ".join(parts)

    if section_name == "language":
        lang = entry.get("language", {})
        lang_name = lang.get("description", "") if isinstance(lang, dict) else str(lang)
        prof = entry.get("proficiency", {})
        prof_desc = prof.get("description", "") if isinstance(prof, dict) else ""
        parts = [lang_name or "Unknown"]
        if prof_desc:
            parts.append(f"({prof_desc})")
        return " ".join(parts)

    if section_name == "careerAspirationPreference":
        return entry.get("description", str(entry))

    if section_name == "careerRolePreference":
        rc = entry.get("roleClassification", {}) or {}
        role = entry.get("role", {}) or {}
        return rc.get("description", "") or role.get("businessTitle", "") or str(entry)

    # Generic fallback
    for key in ("description", "name", "title"):
        if key in entry and entry[key]:
            return str(entry[key])
    return str(entry)[:100]


@tool
def list_profile_entries(section: str) -> dict:
    """List all entries in a profile section with their IDs.

    Use this to find the entry_id needed for edit_entry/remove_entry operations.
    Always call this BEFORE edit_entry or remove_entry so you can resolve which
    entry the user is referring to.

    Args:
        section: The profile section to list. Supported: experience.
    """
    return run_list_profile_entries(section)


def run_list_profile_entries(section: str) -> dict[str, Any]:
    """Implementation -- loads profile, returns entries with IDs and summaries."""
    if not section or not isinstance(section, str):
        return {"success": False, "error": "section is required and must be a non-empty string."}

    section_info = resolve_section(section)
    if section_info is None:
        return {
            "success": False,
            "error": f"Unknown section '{section}'. Supported: {get_valid_section_names()}",
        }

    if section_info.name not in ALLOWED_LIST_SECTIONS:
        return {
            "success": False,
            "error": f"Listing entries for section '{section_info.name}' is not allowed. Only {', '.join(sorted(ALLOWED_LIST_SECTIONS))} is supported.",
        }

    if not section_info.list_field:
        return {
            "success": False,
            "error": f"Section '{section}' is not list-based and does not have individual entries.",
        }

    profile = load_profile()
    normalize_profile(profile)
    core = profile.get("core", {})

    section_data = core.get(section_info.storage_key, {})
    items = section_data.get(section_info.list_field, []) if isinstance(section_data, dict) else []

    entries = []
    for item in items:
        entry_id = item.get("id", "")
        summary = _summarize_entry(section_info.name, item)
        entries.append({"id": entry_id, "summary": summary})

    return {
        "success": True,
        "section": section,
        "count": len(entries),
        "entries": entries,
    }
