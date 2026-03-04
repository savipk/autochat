"""
Tests for core/profile_schema.py — section registry, validation, and storage mappings.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.profile_schema import (
    MAX_FIELD_LENGTH,
    MAX_LIST_ENTRIES,
    SECTION_REGISTRY,
    generate_entry_id,
    get_list_field,
    get_valid_section_names,
    resolve_section,
    resolve_storage_key,
    validate_entry,
    validate_list_size,
)


class TestSectionRegistry:
    def test_all_sections_present(self):
        expected = {
            "experience", "education", "skills",
            "careerAspirationPreference", "careerLocationPreference",
            "careerRolePreference", "language",
        }
        assert expected == set(SECTION_REGISTRY.keys())

    def test_weights_sum_to_100(self):
        total = sum(info.weight for info in SECTION_REGISTRY.values())
        assert total == 100

    def test_education_storage_key_is_qualification(self):
        info = SECTION_REGISTRY["education"]
        assert info.storage_key == "qualification"
        assert info.list_field == "educations"


class TestResolveSection:
    def test_canonical_name(self):
        info = resolve_section("experience")
        assert info is not None
        assert info.storage_key == "experience"

    def test_alias_qualification(self):
        info = resolve_section("qualification")
        assert info is not None
        assert info.name == "education"
        assert info.storage_key == "qualification"

    def test_unknown_section(self):
        assert resolve_section("bogus") is None


class TestResolveStorageKey:
    def test_direct(self):
        assert resolve_storage_key("experience") == "experience"

    def test_alias(self):
        assert resolve_storage_key("qualification") == "qualification"

    def test_education_maps_to_qualification(self):
        assert resolve_storage_key("education") == "qualification"

    def test_unknown(self):
        assert resolve_storage_key("nonexistent") is None


class TestGetListField:
    def test_experience(self):
        assert get_list_field("experience") == "experiences"

    def test_education(self):
        assert get_list_field("education") == "educations"

    def test_skills_none(self):
        assert get_list_field("skills") is None

    def test_unknown(self):
        assert get_list_field("nonexistent") is None


class TestGetValidSectionNames:
    def test_includes_canonical_and_aliases(self):
        names = get_valid_section_names()
        assert "experience" in names
        assert "education" in names
        assert "qualification" in names


class TestValidateEntry:
    def test_valid_experience(self):
        entry = {"jobTitle": "Engineer", "company": "Acme"}
        errors = validate_entry("experience", entry)
        assert errors == []

    def test_missing_required_field(self):
        entry = {"company": "Acme"}
        errors = validate_entry("experience", entry)
        assert len(errors) == 1
        assert "jobTitle" in errors[0]

    def test_empty_required_field(self):
        entry = {"jobTitle": "  ", "company": "Acme"}
        errors = validate_entry("experience", entry)
        assert len(errors) == 1

    def test_oversized_field(self):
        entry = {"jobTitle": "x" * (MAX_FIELD_LENGTH + 1), "company": "Acme"}
        errors = validate_entry("experience", entry)
        assert any("exceeds max length" in e for e in errors)

    def test_valid_education(self):
        entry = {"institutionName": "MIT", "degree": "BS"}
        errors = validate_entry("education", entry)
        assert errors == []

    def test_valid_language(self):
        entry = {"language": {"code": "en", "description": "English"}}
        errors = validate_entry("language", entry)
        assert errors == []

    def test_non_dict_entry(self):
        errors = validate_entry("experience", "not a dict")
        assert len(errors) == 1
        assert "must be a dict" in errors[0]

    def test_unknown_section(self):
        errors = validate_entry("bogus", {"foo": "bar"})
        assert len(errors) == 1
        assert "Unknown section" in errors[0]

    def test_section_without_required_fields(self):
        # Skills has no required_fields
        entry = {"name": "Python"}
        errors = validate_entry("skills", entry)
        assert errors == []


class TestValidateListSize:
    def test_under_limit(self):
        items = [{"id": str(i)} for i in range(10)]
        assert validate_list_size(items, "experience") is None

    def test_over_limit(self):
        items = [{"id": str(i)} for i in range(MAX_LIST_ENTRIES + 1)]
        error = validate_list_size(items, "experience")
        assert error is not None
        assert "exceeding max" in error


class TestGenerateEntryId:
    def test_returns_string(self):
        eid = generate_entry_id()
        assert isinstance(eid, str)
        assert len(eid) > 0

    def test_unique(self):
        ids = {generate_entry_id() for _ in range(100)}
        assert len(ids) == 100
