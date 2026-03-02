"""
Tests for JDDraftManager: save, list, load, load_latest, update_section, finalize.
"""

import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.jd_manager import JDDraftManager

SAMPLE_JD = {
    "title": "GenAI Lead",
    "department": "Technology",
    "level": "Executive Director",
    "sections": {
        "your_team": "We are seeking a GenAI Lead to join our Technology team.",
        "your_role": "- Lead a team of 10 engineers\n- Define AI strategy",
        "your_expertise": "- 8+ years experience\n- Strong Python skills",
    },
}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    """Patch JD_DRAFTS_BASE_DIR to use a temp directory."""
    import core.jd_manager
    monkeypatch.setattr(core.jd_manager, "JD_DRAFTS_BASE_DIR", str(tmp_path / "jd_drafts"))
    return JDDraftManager(username="testuser")


class TestSaveDraft:
    def test_save_returns_draft_id(self, setup):
        draft_id = setup.save_draft(SAMPLE_JD, label="first")
        assert draft_id.startswith("jd_draft_")

    def test_saved_file_exists(self, setup):
        draft_id = setup.save_draft(SAMPLE_JD)
        draft_path = os.path.join(setup._drafts_dir, f"{draft_id}.json")
        assert os.path.exists(draft_path)

    def test_saved_content_matches(self, setup):
        draft_id = setup.save_draft(SAMPLE_JD, label="test")
        loaded = setup.load_draft(draft_id)
        assert loaded["title"] == "GenAI Lead"
        assert loaded["sections"]["your_team"] == SAMPLE_JD["sections"]["your_team"]
        assert loaded["_meta"]["label"] == "test"
        assert loaded["_meta"]["finalized"] is False


class TestListDrafts:
    def test_empty_list(self, setup):
        assert setup.list_drafts() == []

    def test_lists_saved_drafts(self, setup):
        setup.save_draft(SAMPLE_JD, label="a")
        setup.save_draft(SAMPLE_JD, label="b")
        drafts = setup.list_drafts()
        assert len(drafts) == 2
        assert drafts[0]["label"] == "a"
        assert drafts[1]["label"] == "b"

    def test_sorted_oldest_first(self, setup):
        setup.save_draft(SAMPLE_JD, label="first")
        time.sleep(0.01)  # ensure different timestamps
        setup.save_draft(SAMPLE_JD, label="second")
        drafts = setup.list_drafts()
        assert drafts[0]["label"] == "first"
        assert drafts[1]["label"] == "second"


class TestLoadDraft:
    def test_load_existing(self, setup):
        draft_id = setup.save_draft(SAMPLE_JD)
        loaded = setup.load_draft(draft_id)
        assert loaded["title"] == "GenAI Lead"
        assert "_meta" in loaded

    def test_load_nonexistent(self, setup):
        assert setup.load_draft("jd_draft_nonexistent") == {}


class TestLoadLatest:
    def test_no_drafts(self, setup):
        assert setup.load_latest() == {}

    def test_returns_most_recent(self, setup):
        setup.save_draft(SAMPLE_JD, label="old")
        time.sleep(0.01)
        setup.save_draft({**SAMPLE_JD, "title": "Updated Title"}, label="new")
        latest = setup.load_latest()
        assert latest["title"] == "Updated Title"
        assert latest["_meta"]["label"] == "new"


class TestUpdateSection:
    def test_update_creates_new_version(self, setup):
        setup.save_draft(SAMPLE_JD, label="v1")
        new_id = setup.update_section("your_team", "New team description")
        assert new_id.startswith("jd_draft_")
        drafts = setup.list_drafts()
        assert len(drafts) == 2

    def test_updated_content(self, setup):
        setup.save_draft(SAMPLE_JD, label="v1")
        new_id = setup.update_section("your_role", "- Updated responsibilities")
        loaded = setup.load_draft(new_id)
        assert loaded["sections"]["your_role"] == "- Updated responsibilities"
        # Other sections remain unchanged
        assert loaded["sections"]["your_team"] == SAMPLE_JD["sections"]["your_team"]

    def test_update_no_existing_draft(self, setup):
        result = setup.update_section("your_team", "content")
        assert result == ""

    def test_update_label_default(self, setup):
        setup.save_draft(SAMPLE_JD)
        new_id = setup.update_section("your_expertise", "New content")
        loaded = setup.load_draft(new_id)
        assert loaded["_meta"]["label"] == "Updated your_expertise"


class TestFinalize:
    def test_finalize_marks_draft(self, setup):
        setup.save_draft(SAMPLE_JD)
        final_id = setup.finalize()
        assert final_id.startswith("jd_draft_")
        loaded = setup.load_draft(final_id)
        assert loaded["_meta"]["finalized"] is True
        assert loaded["_meta"]["label"] == "Finalized"

    def test_finalize_no_drafts(self, setup):
        assert setup.finalize() == ""

    def test_finalize_preserves_content(self, setup):
        setup.save_draft(SAMPLE_JD)
        final_id = setup.finalize()
        loaded = setup.load_draft(final_id)
        assert loaded["title"] == "GenAI Lead"
        assert loaded["sections"]["your_team"] == SAMPLE_JD["sections"]["your_team"]
