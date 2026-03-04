"""
Tests for core/profile_score.py — shared completion scoring.
"""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.profile_manager import ProfileManager
from core.profile_score import compute_completion_score, compute_section_scores, get_missing_sections, normalize_profile


FULL_PROFILE = {
    "core": {
        "experience": {"experiences": [{"jobTitle": "Eng"}]},
        "qualification": {"educations": [{"institutionName": "MIT"}]},
        "skills": {"top": [{"name": "Python"}], "additional": []},
        "careerAspirationPreference": {"preferredAspirations": [{"code": "x"}]},
        "careerLocationPreference": {"preferredRelocationRegions": [{"code": "US"}]},
        "careerRolePreference": {"preferredRoles": [{"code": "dev"}]},
        "language": {"languages": [{"language": {"code": "en"}}]},
    }
}

EMPTY_PROFILE = {"core": {"name": {"businessFirstName": "Test"}}}


class TestComputeCompletionScore:
    def test_full_profile_is_100(self):
        assert compute_completion_score(FULL_PROFILE) == 100

    def test_empty_profile_is_0(self):
        assert compute_completion_score(EMPTY_PROFILE) == 0

    def test_empty_dict_is_0(self):
        assert compute_completion_score({}) == 0

    def test_no_core_key_is_0(self):
        assert compute_completion_score({"email": "x@y.com"}) == 0

    def test_partial_profile(self):
        profile = {
            "core": {
                "experience": {"experiences": [{"jobTitle": "Eng"}]},
                "skills": {"top": [{"name": "Python"}]},
            }
        }
        score = compute_completion_score(profile)
        # experience=25, skills=20 → 45/100 = 45
        assert score == 45

    def test_location_no_relocation(self):
        """Location counts if timeline code is NO (no relocation wanted)."""
        profile = {
            "core": {
                "careerLocationPreference": {
                    "preferredRelocationTimeline": {"code": "NO"},
                }
            }
        }
        score = compute_completion_score(profile)
        assert score == 10  # only location weight

    def test_normalizes_root_to_core(self):
        """Root-level data is normalized into core before scoring."""
        root_profile = {
            "experience": {"experiences": [{"jobTitle": "Eng"}]},
            "core": {},
        }
        # After normalization, experience should be found in core
        assert compute_completion_score(root_profile) == 25


class TestComputeSectionScores:
    def test_full_profile_all_scored(self):
        scores = compute_section_scores(FULL_PROFILE)
        assert scores["experience"] == 25
        assert scores["qualification"] == 15
        assert scores["skills"] == 20
        assert scores["careerAspirationPreference"] == 10
        assert scores["careerLocationPreference"] == 10
        assert scores["careerRolePreference"] == 10
        assert scores["language"] == 10

    def test_empty_profile_all_zero(self):
        scores = compute_section_scores(EMPTY_PROFILE)
        assert all(v == 0 for v in scores.values())

    def test_keys_are_storage_keys(self):
        scores = compute_section_scores(FULL_PROFILE)
        # education's storage key is "qualification"
        assert "qualification" in scores


class TestGetMissingSections:
    def test_full_profile_no_missing(self):
        assert get_missing_sections(FULL_PROFILE) == []

    def test_empty_profile_all_missing(self):
        missing = get_missing_sections(EMPTY_PROFILE)
        assert len(missing) == 7

    def test_partial_profile(self):
        profile = {
            "core": {
                "experience": {"experiences": [{"jobTitle": "Eng"}]},
            }
        }
        missing = get_missing_sections(profile)
        assert "experience" not in missing
        assert "qualification" in missing
        assert "skills" in missing


class TestNormalizeProfile:
    def test_copies_root_to_core(self):
        profile = {
            "experience": {"experiences": [{"jobTitle": "Eng"}]},
            "skills": {"top": [{"name": "Python"}]},
            "core": {"name": {"businessFirstName": "Test"}},
        }
        normalize_profile(profile)
        assert "experience" in profile["core"]
        assert "skills" in profile["core"]
        # Original core data preserved
        assert profile["core"]["name"]["businessFirstName"] == "Test"

    def test_skips_null_root_values(self):
        """Root-level null values should NOT be copied into core."""
        profile = {
            "skills": None,
            "experience": {"experiences": [{"jobTitle": "Eng"}]},
            "core": {},
        }
        normalize_profile(profile)
        # null skills should not appear in core
        assert "skills" not in profile["core"]
        # non-null sections still copied
        assert "experience" in profile["core"]

    def test_does_not_overwrite_existing_core_data(self):
        profile = {
            "experience": {"experiences": [{"jobTitle": "Root"}]},
            "core": {
                "experience": {"experiences": [{"jobTitle": "Core"}]},
            },
        }
        normalize_profile(profile)
        # core data should NOT be overwritten
        assert profile["core"]["experience"]["experiences"][0]["jobTitle"] == "Core"

    def test_creates_core_if_missing(self):
        profile = {"experience": {"experiences": [{"jobTitle": "Eng"}]}}
        normalize_profile(profile)
        assert "core" in profile
        assert "experience" in profile["core"]

    def test_copies_completion_score(self):
        profile = {"completionScore": 85, "core": {}}
        normalize_profile(profile)
        assert profile["core"]["completionScore"] == 85

    def test_all_sections_normalized(self):
        """All 7 sections at root level are normalized into core."""
        profile = {
            "experience": {"experiences": [{"jobTitle": "Eng"}]},
            "qualification": {"educations": [{"institutionName": "MIT"}]},
            "skills": {"top": [{"name": "Python"}]},
            "careerAspirationPreference": {"preferredAspirations": [{"code": "x"}]},
            "careerLocationPreference": {"preferredRelocationRegions": [{"code": "US"}]},
            "careerRolePreference": {"preferredRoles": [{"code": "dev"}]},
            "language": {"languages": [{"language": {"code": "en"}}]},
            "core": {},
        }
        normalize_profile(profile)
        score = compute_completion_score(profile)
        assert score == 100


class TestProfileManagerRecalculatesScore:
    """Verify ProfileManager.submit() and rollback() recalculate completionScore."""

    def _make_manager(self, tmp_path):
        profile_path = os.path.join(str(tmp_path), "profile.json")
        return ProfileManager(username="testuser", profile_path=profile_path)

    def test_submit_recalculates_score(self, tmp_path):
        """submit() should compute a fresh completionScore before writing."""
        mgr = self._make_manager(tmp_path)

        # Profile with stale score of 0 but data that should yield 45
        profile = {
            "completionScore": 0,
            "core": {
                "experience": {"experiences": [{"jobTitle": "Eng"}]},
                "skills": {"top": [{"name": "Python"}]},
            },
        }
        mgr.submit(profile)

        with open(mgr.profile_path, "r") as f:
            saved = json.load(f)

        assert saved["completionScore"] == 45

    def test_submit_strips_meta(self, tmp_path):
        """submit() should still strip _meta even with score recalculation."""
        mgr = self._make_manager(tmp_path)
        profile = {"_meta": {"draft_id": "x"}, "core": {}}
        mgr.submit(profile)

        with open(mgr.profile_path, "r") as f:
            saved = json.load(f)

        assert "_meta" not in saved

    def test_rollback_recalculates_score(self, tmp_path):
        """rollback() should compute a fresh completionScore for restored data."""
        mgr = self._make_manager(tmp_path)

        # Write an initial profile (this becomes the backup source)
        initial = {
            "completionScore": 0,
            "core": {
                "experience": {"experiences": [{"jobTitle": "Eng"}]},
                "skills": {"top": [{"name": "Python"}]},
            },
        }
        mgr.submit(initial)

        # Now submit a different profile (backup of initial is created)
        updated = {"completionScore": 0, "core": {}}
        mgr.submit(updated)

        # Rollback should restore initial data with recalculated score
        restored = mgr.rollback()
        assert restored is not None
        assert restored["completionScore"] == 45

        # Verify the file on disk also has the recalculated score
        with open(mgr.profile_path, "r") as f:
            on_disk = json.load(f)
        assert on_disk["completionScore"] == 45
