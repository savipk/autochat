"""
Profile schema — single source of truth for section metadata, validation, and storage mappings.

All section names, storage keys, list fields, weights, and required-field
definitions live here so that tools, adapters, and scoring logic stay consistent.
"""

from __future__ import annotations

import uuid
from typing import Any

# Maximum length for any single string field value
MAX_FIELD_LENGTH = 500

# Maximum number of entries in any list-based section
MAX_LIST_ENTRIES = 50


class SectionInfo:
    """Metadata for one editable profile section."""

    __slots__ = ("name", "storage_key", "list_field", "weight", "required_fields")

    def __init__(
        self,
        name: str,
        storage_key: str,
        list_field: str | None,
        weight: int,
        required_fields: tuple[str, ...] = (),
    ):
        self.name = name
        self.storage_key = storage_key
        self.list_field = list_field
        self.weight = weight
        self.required_fields = required_fields


# Canonical registry — tool-facing name → section metadata
SECTION_REGISTRY: dict[str, SectionInfo] = {
    "experience": SectionInfo(
        name="experience",
        storage_key="experience",
        list_field="experiences",
        weight=25,
        required_fields=("jobTitle",),
    ),
    "education": SectionInfo(
        name="education",
        storage_key="qualification",
        list_field="educations",
        weight=15,
        required_fields=("institutionName",),
    ),
    "skills": SectionInfo(
        name="skills",
        storage_key="skills",
        list_field=None,  # skills have a special structure (top/additional)
        weight=20,
    ),
    "careerAspirationPreference": SectionInfo(
        name="careerAspirationPreference",
        storage_key="careerAspirationPreference",
        list_field="preferredAspirations",
        weight=10,
    ),
    "careerLocationPreference": SectionInfo(
        name="careerLocationPreference",
        storage_key="careerLocationPreference",
        list_field=None,  # complex nested structure
        weight=10,
    ),
    "careerRolePreference": SectionInfo(
        name="careerRolePreference",
        storage_key="careerRolePreference",
        list_field="preferredRoles",
        weight=10,
    ),
    "language": SectionInfo(
        name="language",
        storage_key="language",
        list_field="languages",
        weight=10,
        required_fields=("language",),
    ),
}

# Aliases — allow callers to use either the tool-facing name or the storage key
_ALIASES: dict[str, str] = {
    "qualification": "education",
}


def resolve_section(section: str) -> SectionInfo | None:
    """Look up a section by tool-facing name or alias. Returns *None* if unknown."""
    canonical = _ALIASES.get(section, section)
    return SECTION_REGISTRY.get(canonical)


def resolve_storage_key(section: str) -> str | None:
    """Return the profile-JSON key for *section*, or *None* if unknown."""
    info = resolve_section(section)
    return info.storage_key if info else None


def get_list_field(section: str) -> str | None:
    """Return the inner array field name for *section*, or *None*."""
    info = resolve_section(section)
    return info.list_field if info else None


def get_valid_section_names() -> list[str]:
    """Return all accepted section names (canonical + aliases)."""
    return list(SECTION_REGISTRY.keys()) + list(_ALIASES.keys())


def validate_entry(section: str, entry: dict[str, Any]) -> list[str]:
    """Validate a single entry dict for *section*.

    Returns a list of error strings. Empty list means valid.
    """
    errors: list[str] = []
    info = resolve_section(section)
    if info is None:
        errors.append(f"Unknown section: {section}")
        return errors

    if not isinstance(entry, dict):
        errors.append(f"Entry must be a dict, got {type(entry).__name__}")
        return errors

    # Check required fields
    for field in info.required_fields:
        val = entry.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Missing required field '{field}' for section '{info.name}'")

    # Check string field lengths
    for key, val in entry.items():
        if isinstance(val, str) and len(val) > MAX_FIELD_LENGTH:
            errors.append(
                f"Field '{key}' exceeds max length {MAX_FIELD_LENGTH} "
                f"(got {len(val)} chars)"
            )

    return errors


def validate_list_size(items: list, section: str) -> str | None:
    """Return an error string if *items* exceeds MAX_LIST_ENTRIES, else None."""
    if len(items) > MAX_LIST_ENTRIES:
        return (
            f"Section '{section}' would have {len(items)} entries, "
            f"exceeding max of {MAX_LIST_ENTRIES}"
        )
    return None


def generate_entry_id() -> str:
    """Generate a new UUID string for a profile entry."""
    return str(uuid.uuid4())
