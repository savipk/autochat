"""
Update profile tool -- supports all editable profile sections with persistence.

Supports CRUD operations: merge (default), replace, add_entry, edit_entry, remove_entry.
"""

from __future__ import annotations

import copy
from typing import Any

import chainlit as cl
from langchain_core.tools import tool

from core.profile import load_profile
from core.profile_manager import ProfileManager
from core.profile_schema import (
    generate_entry_id,
    get_list_field,
    get_valid_section_names,
    resolve_section,
    validate_entry,
    validate_list_size,
)
from core.profile_score import compute_completion_score, normalize_profile

VALID_OPERATIONS = ("merge", "replace", "add_entry", "edit_entry", "remove_entry")


def _get_user_context() -> tuple[str, str]:
    """Extract username and profile_path from the Chainlit session."""
    try:
        user = cl.user_session.get("user")
        if user and hasattr(user, "metadata") and user.metadata:
            return user.identifier, user.metadata.get("profile_path", "")
    except Exception:
        pass
    return "", ""


def _normalize_skill(skill: Any) -> dict:
    """Convert a flat skill string to the structured format used in the profile."""
    if isinstance(skill, dict):
        if "name" not in skill:
            return skill
        # Already structured
        skill.setdefault("id", generate_entry_id())
        skill.setdefault("source", "MANUAL")
        return skill
    # Flat string → structured object
    return {"id": generate_entry_id(), "source": "MANUAL", "name": str(skill)}


def _normalize_skills_list(skills: list) -> list[dict]:
    """Normalize a list of skills (strings or dicts) to structured format."""
    return [_normalize_skill(s) for s in skills]


def _deduplicate_skills(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge new skills into existing, deduplicating by name (case-insensitive)."""
    seen = {s["name"].lower() for s in existing if isinstance(s, dict) and "name" in s}
    result = list(existing)
    for s in new:
        name = s.get("name", "") if isinstance(s, dict) else str(s)
        if name.lower() not in seen:
            seen.add(name.lower())
            result.append(s)
    return result


def _apply_skills_update(
    core: dict, updates: dict, operation: str
) -> dict:
    """Apply skills-specific update logic. Returns the normalized updates dict."""
    # Normalize flat skills list
    if "skills" in updates and isinstance(updates["skills"], list):
        flat = updates["skills"]
        updates = {
            "topSkills": flat[:3],
            "additionalSkills": flat[3:],
        }

    if core.get("skills") is None:
        core["skills"] = {}
    core.setdefault("skills", {})
    existing_top = core["skills"].get("top", [])
    existing_additional = core["skills"].get("additional", [])

    if operation == "replace":
        if "topSkills" in updates:
            core["skills"]["top"] = _normalize_skills_list(updates["topSkills"])
        if "additionalSkills" in updates:
            core["skills"]["additional"] = _normalize_skills_list(updates["additionalSkills"])
    else:
        # merge (default) — deduplicate
        if "topSkills" in updates:
            new_top = _normalize_skills_list(updates["topSkills"])
            core["skills"]["top"] = _deduplicate_skills(existing_top, new_top)
        if "additionalSkills" in updates:
            new_additional = _normalize_skills_list(updates["additionalSkills"])
            core["skills"]["additional"] = _deduplicate_skills(
                existing_additional, new_additional
            )

    return updates


def _apply_list_section_update(
    core: dict,
    section_info: Any,
    updates: dict,
    operation: str,
    entry_id: str | None,
) -> tuple[dict, str | None]:
    """Apply update to a list-based section. Returns (updates, error)."""
    storage_key = section_info.storage_key
    list_field = section_info.list_field

    section_data = core.setdefault(storage_key, {})
    existing_items = section_data.get(list_field, [])

    if operation == "replace":
        core[storage_key] = updates
        return updates, None

    if operation == "add_entry":
        entry = updates
        # Validate the entry
        errors = validate_entry(section_info.name, entry)
        if errors:
            return updates, "; ".join(errors)
        entry.setdefault("id", generate_entry_id())
        existing_items.append(entry)
        section_data[list_field] = existing_items
        # Check list size
        size_err = validate_list_size(existing_items, section_info.name)
        if size_err:
            existing_items.pop()  # rollback
            return updates, size_err
        return entry, None

    if operation == "edit_entry":
        if not entry_id:
            return updates, "entry_id is required for edit_entry operation."
        found = False
        for i, item in enumerate(existing_items):
            if item.get("id") == entry_id:
                # Shallow merge
                existing_items[i] = {**item, **updates}
                found = True
                break
        if not found:
            return updates, f"No entry found with id '{entry_id}'."
        section_data[list_field] = existing_items
        return updates, None

    if operation == "remove_entry":
        if not entry_id:
            return updates, "entry_id is required for remove_entry operation."
        original_len = len(existing_items)
        existing_items = [item for item in existing_items if item.get("id") != entry_id]
        if len(existing_items) == original_len:
            return updates, f"No entry found with id '{entry_id}'."
        section_data[list_field] = existing_items
        return updates, None

    # merge (default) — append new entries, don't remove existing
    if list_field and list_field in updates:
        new_items = updates[list_field]
        if isinstance(new_items, list):
            for entry in new_items:
                errors = validate_entry(section_info.name, entry)
                if errors:
                    return updates, f"Invalid entry: {'; '.join(errors)}"
                entry.setdefault("id", generate_entry_id())
            merged = existing_items + new_items
            size_err = validate_list_size(merged, section_info.name)
            if size_err:
                return updates, size_err
            section_data[list_field] = merged
    else:
        # Non-list merge: shallow-merge the dict
        core[storage_key] = {**section_data, **updates}

    return updates, None


@tool
def update_profile(
    section: str = "skills",
    updates: dict | None = None,
    operation: str = "merge",
    entry_id: str | None = None,
) -> dict:
    """Updates sections of the user's profile.

    Args:
        section: The profile section to update. Supported: skills, experience,
                 education (alias: qualification), careerAspirationPreference,
                 careerLocationPreference, careerRolePreference, language.
        updates: Dict with section-specific updates. For skills, pass
                 {"skills": ["Python", "Docker", ...]} as a flat list, or
                 {"topSkills": [...], "additionalSkills": [...]} for explicit placement.
                 For add_entry, pass the single entry dict directly.
        operation: One of "merge" (default, appends without removing existing),
                   "replace" (full overwrite), "add_entry" (append one entry),
                   "edit_entry" (update entry matching entry_id),
                   "remove_entry" (remove entry matching entry_id).
        entry_id: Required for edit_entry and remove_entry operations.
    """
    return run_update_profile(
        section=section, updates=updates, operation=operation, entry_id=entry_id
    )


def run_update_profile(
    section: str = "skills",
    updates: dict[str, Any] | None = None,
    operation: str = "merge",
    entry_id: str | None = None,
) -> dict[str, Any]:
    """Actual implementation -- loads profile, applies updates, persists via ProfileManager."""
    if not section or not isinstance(section, str):
        return {"success": False, "error": "section is required and must be a non-empty string."}

    section_info = resolve_section(section)
    if section_info is None:
        return {
            "success": False,
            "error": f"Update for section '{section}' is not yet supported. Supported: {get_valid_section_names()}",
        }

    if operation not in VALID_OPERATIONS:
        return {
            "success": False,
            "error": f"Invalid operation '{operation}'. Must be one of: {VALID_OPERATIONS}",
        }

    if operation in ("edit_entry", "remove_entry") and not entry_id:
        return {"success": False, "error": f"entry_id is required for {operation} operation."}

    username, profile_path = _get_user_context()
    profile = load_profile(profile_path or None)
    normalize_profile(profile)
    prev_score = compute_completion_score(profile)

    if not updates:
        if section == "skills" and operation not in ("remove_entry",):
            updates = {
                "topSkills": ["A2A", "MCP", "RAG"],
                "additionalSkills": ["Context Engineering", "Azure Open AI", "Azure AI Search"],
            }
        elif operation == "remove_entry":
            # remove_entry doesn't need updates, just entry_id
            updates = {}
        else:
            return {"success": False, "error": "updates dict is required for non-skills sections."}

    # Apply updates to profile
    core = profile.setdefault("core", {})
    error = None

    if section_info.name == "skills":
        updates = _apply_skills_update(core, updates, operation)
    elif section_info.list_field:
        updates, error = _apply_list_section_update(
            core, section_info, updates, operation, entry_id
        )
    else:
        # Non-list sections (careerLocationPreference, etc.)
        if operation == "replace" or operation == "merge":
            existing = core.get(section_info.storage_key, {})
            if operation == "merge" and isinstance(existing, dict):
                core[section_info.storage_key] = {**existing, **updates}
            else:
                core[section_info.storage_key] = updates
        else:
            error = f"Operation '{operation}' is not supported for section '{section_info.name}' (not a list-based section)."

    if error:
        return {"success": False, "error": error}

    # Persist — fail explicitly if we can't persist
    if username and profile_path:
        mgr = ProfileManager(username=username, profile_path=profile_path)
        mgr.submit(profile)
    else:
        return {
            "success": False,
            "error": "Cannot persist profile update: missing username or profile_path in session.",
            "section": section,
            "updated_fields": updates,
        }

    new_score = compute_completion_score(profile)

    return {
        "success": True,
        "error": None,
        "section": section,
        "operation": operation,
        "updated_fields": updates,
        "previous_completion_score": prev_score,
        "estimated_new_score": new_score,
        "profile_path": profile_path,
        "username": username,
    }
