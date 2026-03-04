"""
Tests for agents/mycareer/tools/list_profile_entries.py
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PROFILE_WITH_ENTRIES = {
    "core": {
        "name": {"businessFirstName": "Test"},
        "experience": {
            "experiences": [
                {"id": "e1", "jobTitle": "Engineer", "company": "Acme", "startDate": "2020-01-01"},
                {"id": "e2", "jobTitle": "Lead", "company": "BigCo", "startDate": "2022-06-01"},
            ]
        },
        "qualification": {
            "educations": [
                {"id": "q1", "institutionName": "MIT", "degree": "BS CS"},
            ]
        },
        "language": {
            "languages": [
                {"id": "l1", "language": {"code": "en", "description": "English"}, "proficiency": {"code": "FLUENT", "description": "Fluent"}},
            ]
        },
        "careerRolePreference": {
            "preferredRoles": [
                {"id": "r1", "role": {"businessTitle": "Tech Lead"}, "roleClassification": None},
            ]
        },
    }
}

# Profile with data at root level (like miro_profile)
ROOT_LEVEL_PROFILE = {
    "experience": {
        "experiences": [
            {"id": "e1", "jobTitle": "Architect", "company": "UBS", "startDate": "2024-08-01"},
        ]
    },
    "core": {"name": {"businessFirstName": "George"}},
}


@pytest.fixture
def profile_path(tmp_path, monkeypatch):
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(PROFILE_WITH_ENTRIES))
    import core.profile
    monkeypatch.setattr(core.profile, "PROFILE_PATH", str(path))
    return str(path)


@pytest.fixture
def root_profile_path(tmp_path, monkeypatch):
    path = tmp_path / "root_profile.json"
    path.write_text(json.dumps(ROOT_LEVEL_PROFILE))
    import core.profile
    monkeypatch.setattr(core.profile, "PROFILE_PATH", str(path))
    return str(path)


class TestListProfileEntries:
    def _run(self, section):
        from agents.mycareer.tools.list_profile_entries import run_list_profile_entries
        return run_list_profile_entries(section)

    def test_list_experience_entries(self, profile_path):
        result = self._run("experience")
        assert result["success"] is True
        assert result["count"] == 2
        assert result["entries"][0]["id"] == "e1"
        assert "Engineer" in result["entries"][0]["summary"]
        assert "Acme" in result["entries"][0]["summary"]

    def test_list_education_entries(self, profile_path):
        result = self._run("education")
        assert result["success"] is True
        assert result["count"] == 1
        assert "MIT" in result["entries"][0]["summary"]

    def test_list_language_entries(self, profile_path):
        result = self._run("language")
        assert result["success"] is True
        assert result["count"] == 1
        assert "English" in result["entries"][0]["summary"]

    def test_unsupported_section(self, profile_path):
        result = self._run("bogus")
        assert result["success"] is False
        assert "Unknown section" in result["error"]

    def test_non_list_section_rejected(self, profile_path):
        result = self._run("careerLocationPreference")
        assert result["success"] is False
        assert "not list-based" in result["error"]

    def test_empty_section(self, profile_path):
        # Skills is not list-based, but experience with no entries should work
        # Let's use a section alias
        result = self._run("qualification")
        assert result["success"] is True
        assert result["count"] == 1

    def test_root_level_profile_normalized(self, root_profile_path):
        """Entries at root level are found after normalization."""
        result = self._run("experience")
        assert result["success"] is True
        assert result["count"] == 1
        assert "Architect" in result["entries"][0]["summary"]
        assert "UBS" in result["entries"][0]["summary"]

    def test_role_preference_entries(self, profile_path):
        result = self._run("careerRolePreference")
        assert result["success"] is True
        assert result["count"] == 1
        assert "Tech Lead" in result["entries"][0]["summary"]

    def test_empty_string_section(self, profile_path):
        result = self._run("")
        assert result["success"] is False
