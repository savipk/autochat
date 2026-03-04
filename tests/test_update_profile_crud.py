"""
Tests for update_profile CRUD operations, validation, and merge behavior.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SAMPLE_PROFILE = {
    "core": {
        "name": {"businessFirstName": "Test", "businessLastName": "User"},
        "experience": {
            "experiences": [
                {
                    "id": "exp-1",
                    "jobTitle": "Engineer",
                    "company": "Acme",
                    "startDate": "2020-01-01",
                },
                {
                    "id": "exp-2",
                    "jobTitle": "Senior Engineer",
                    "company": "BigCo",
                    "startDate": "2022-01-01",
                },
            ]
        },
        "skills": {
            "top": [
                {"id": "sk-1", "source": "AI_INFERRED", "name": "Python"},
                {"id": "sk-2", "source": "AI_INFERRED", "name": "Docker"},
            ],
            "additional": [
                {"id": "sk-3", "source": "MANUAL", "name": "Go"},
            ],
        },
        "qualification": {
            "educations": [
                {"id": "edu-1", "institutionName": "MIT", "degree": "BS CS"},
            ]
        },
    }
}


@pytest.fixture
def profile_path(tmp_path, monkeypatch):
    """Write sample profile and patch PROFILE_PATH + user context."""
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(SAMPLE_PROFILE))
    import core.profile
    monkeypatch.setattr(core.profile, "PROFILE_PATH", str(path))
    return str(path)


@pytest.fixture
def mock_user_context(profile_path, monkeypatch):
    """Mock _get_user_context to return test values and patch ProfileManager."""
    import agents.mycareer.tools.update_profile  # noqa: F401 — ensure module is loaded
    umod = sys.modules["agents.mycareer.tools.update_profile"]
    monkeypatch.setattr(umod, "_get_user_context", lambda: ("testuser", profile_path))

    import core.profile_manager
    monkeypatch.setattr(core.profile_manager, "DRAFTS_BASE_DIR", str(os.path.dirname(profile_path)))
    return profile_path


def _run(**kwargs):
    from agents.mycareer.tools.update_profile import run_update_profile
    return run_update_profile(**kwargs)


class TestInvalidInputs:
    def test_invalid_section(self, profile_path, mock_user_context):
        result = _run(section="bogus")
        assert result["success"] is False
        assert "not yet supported" in result["error"]

    def test_invalid_operation(self, profile_path, mock_user_context):
        result = _run(section="experience", operation="destroy")
        assert result["success"] is False
        assert "Invalid operation" in result["error"]

    def test_edit_entry_without_id(self, profile_path, mock_user_context):
        result = _run(section="experience", operation="edit_entry", updates={"jobTitle": "X"})
        assert result["success"] is False
        assert "entry_id is required" in result["error"]

    def test_remove_entry_without_id(self, profile_path, mock_user_context):
        result = _run(section="experience", operation="remove_entry")
        assert result["success"] is False
        assert "entry_id is required" in result["error"]

    def test_qualification_alias_accepted(self, profile_path, mock_user_context):
        result = _run(
            section="qualification",
            operation="add_entry",
            updates={"institutionName": "Stanford", "degree": "MS"},
        )
        assert result["success"] is True


class TestMergeOperation:
    def test_merge_appends_experiences(self, profile_path, mock_user_context):
        new_exp = {
            "experiences": [
                {"jobTitle": "Manager", "company": "NewCo"}
            ]
        }
        result = _run(section="experience", operation="merge", updates=new_exp)
        assert result["success"] is True

        # Verify existing experiences preserved
        profile = json.loads(open(profile_path).read())
        exps = profile["core"]["experience"]["experiences"]
        assert len(exps) == 3
        assert exps[0]["id"] == "exp-1"
        assert exps[2]["jobTitle"] == "Manager"

    def test_merge_skills_deduplicates(self, profile_path, mock_user_context):
        result = _run(
            section="skills",
            operation="merge",
            updates={"topSkills": ["Python", "Kubernetes"]},
        )
        assert result["success"] is True

        profile = json.loads(open(profile_path).read())
        top = profile["core"]["skills"]["top"]
        names = [s["name"] for s in top]
        # Python should appear only once (deduped), Kubernetes added
        assert names.count("Python") == 1
        assert "Kubernetes" in names


class TestReplaceOperation:
    def test_replace_overwrites_section(self, profile_path, mock_user_context):
        new_exp = {"experiences": [{"jobTitle": "CTO", "company": "Startup"}]}
        result = _run(section="experience", operation="replace", updates=new_exp)
        assert result["success"] is True

        profile = json.loads(open(profile_path).read())
        exps = profile["core"]["experience"]["experiences"]
        assert len(exps) == 1
        assert exps[0]["jobTitle"] == "CTO"


class TestAddEntry:
    def test_add_experience_entry(self, profile_path, mock_user_context):
        entry = {"jobTitle": "VP", "company": "MegaCorp", "startDate": "2024-01-01"}
        result = _run(section="experience", operation="add_entry", updates=entry)
        assert result["success"] is True

        profile = json.loads(open(profile_path).read())
        exps = profile["core"]["experience"]["experiences"]
        assert len(exps) == 3
        assert exps[2]["jobTitle"] == "VP"
        assert "id" in exps[2]  # auto-generated

    def test_add_entry_validates_required_fields(self, profile_path, mock_user_context):
        entry = {"company": "NoTitle Inc."}  # missing jobTitle
        result = _run(section="experience", operation="add_entry", updates=entry)
        assert result["success"] is False
        assert "jobTitle" in result["error"]

    def test_add_education_entry(self, profile_path, mock_user_context):
        entry = {"institutionName": "Stanford", "degree": "MS"}
        result = _run(section="education", operation="add_entry", updates=entry)
        assert result["success"] is True

        profile = json.loads(open(profile_path).read())
        edus = profile["core"]["qualification"]["educations"]
        assert len(edus) == 2


class TestEditEntry:
    def test_edit_experience_entry(self, profile_path, mock_user_context):
        result = _run(
            section="experience",
            operation="edit_entry",
            entry_id="exp-1",
            updates={"jobTitle": "Lead Engineer", "company": "Acme Corp"},
        )
        assert result["success"] is True

        profile = json.loads(open(profile_path).read())
        exp = next(e for e in profile["core"]["experience"]["experiences"] if e["id"] == "exp-1")
        assert exp["jobTitle"] == "Lead Engineer"
        assert exp["company"] == "Acme Corp"
        assert exp["startDate"] == "2020-01-01"  # preserved

    def test_edit_nonexistent_entry(self, profile_path, mock_user_context):
        result = _run(
            section="experience",
            operation="edit_entry",
            entry_id="nonexistent",
            updates={"jobTitle": "X"},
        )
        assert result["success"] is False
        assert "No entry found" in result["error"]


class TestRemoveEntry:
    def test_remove_experience_entry(self, profile_path, mock_user_context):
        result = _run(section="experience", operation="remove_entry", entry_id="exp-1")
        assert result["success"] is True

        profile = json.loads(open(profile_path).read())
        exps = profile["core"]["experience"]["experiences"]
        assert len(exps) == 1
        assert exps[0]["id"] == "exp-2"

    def test_remove_nonexistent_entry(self, profile_path, mock_user_context):
        result = _run(section="experience", operation="remove_entry", entry_id="nonexistent")
        assert result["success"] is False
        assert "No entry found" in result["error"]


class TestSkillsNormalization:
    def test_flat_skills_list_normalized(self, profile_path, mock_user_context):
        result = _run(
            section="skills",
            operation="replace",
            updates={"skills": ["A", "B", "C", "D"]},
        )
        assert result["success"] is True

        profile = json.loads(open(profile_path).read())
        top = profile["core"]["skills"]["top"]
        additional = profile["core"]["skills"]["additional"]
        # Should be structured objects now
        assert all(isinstance(s, dict) and "name" in s for s in top)
        assert all(isinstance(s, dict) and "name" in s for s in additional)
        assert [s["name"] for s in top] == ["A", "B", "C"]
        assert [s["name"] for s in additional] == ["D"]

    def test_merge_preserves_existing_skills(self, profile_path, mock_user_context):
        result = _run(
            section="skills",
            operation="merge",
            updates={"additionalSkills": ["Go", "Rust"]},
        )
        assert result["success"] is True

        profile = json.loads(open(profile_path).read())
        additional = profile["core"]["skills"]["additional"]
        names = [s["name"] for s in additional]
        # Go existed already, should be deduped; Rust is new
        assert names.count("Go") == 1
        assert "Rust" in names


class TestPersistenceFailure:
    def test_no_user_context_fails(self, profile_path, monkeypatch):
        """Without user context, update should return success=False."""
        import agents.mycareer.tools.update_profile  # noqa: F401
        umod = sys.modules["agents.mycareer.tools.update_profile"]
        monkeypatch.setattr(umod, "_get_user_context", lambda: ("", ""))

        import core.profile
        monkeypatch.setattr(core.profile, "PROFILE_PATH", profile_path)

        result = _run(section="skills", updates={"topSkills": ["X"]})
        assert result["success"] is False
        assert "Cannot persist" in result["error"]


class TestScoreConsistency:
    def test_scores_match_shared_scorer(self, profile_path, mock_user_context):
        """Verify update_profile uses the same scorer as profile_analyzer."""
        from core.profile_score import compute_completion_score

        with open(profile_path) as f:
            profile = json.load(f)
        expected = compute_completion_score(profile)

        result = _run(section="skills", updates={"topSkills": ["NewSkill"]})
        assert result["previous_completion_score"] == expected
