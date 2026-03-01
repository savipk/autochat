"""
Tests for ProfileManager: CRUD, drafts, submit with backup, _meta stripping.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.profile_manager import ProfileManager

SAMPLE_PROFILE = {
    "core": {
        "name": {"businessFirstName": "Test", "businessLastName": "User"},
        "completionScore": 50,
    }
}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    """Create a temp profile and patch DRAFTS_BASE_DIR."""
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(SAMPLE_PROFILE))

    import core.profile_manager
    monkeypatch.setattr(core.profile_manager, "DRAFTS_BASE_DIR", str(tmp_path / "drafts"))

    return ProfileManager(username="testuser", profile_path=str(profile_path))


class TestLoadCurrent:
    def test_loads_valid_profile(self, setup):
        data = setup.load_current()
        assert data["core"]["name"]["businessFirstName"] == "Test"

    def test_returns_empty_for_missing_file(self, tmp_path):
        mgr = ProfileManager("x", str(tmp_path / "nonexistent.json"))
        assert mgr.load_current() == {}


class TestDrafts:
    def test_save_and_list_drafts(self, setup):
        setup.save_draft(SAMPLE_PROFILE, label="first")
        drafts = setup.list_drafts()
        assert len(drafts) == 1
        assert drafts[0]["label"] == "first"

    def test_load_draft_by_id(self, setup):
        draft_id = setup.save_draft({"foo": "bar"}, label="test")
        loaded = setup.load_draft(draft_id)
        assert loaded["foo"] == "bar"
        assert loaded["_meta"]["draft_id"] == draft_id

    def test_multiple_drafts_sorted(self, setup):
        setup.save_draft(SAMPLE_PROFILE, label="a")
        setup.save_draft(SAMPLE_PROFILE, label="b")
        setup.save_draft(SAMPLE_PROFILE, label="c")
        drafts = setup.list_drafts()
        assert len(drafts) == 3
        assert drafts[0]["label"] == "a"
        assert drafts[2]["label"] == "c"

    def test_load_nonexistent_draft(self, setup):
        assert setup.load_draft("draft_nonexistent") == {}

    def test_list_drafts_empty(self, setup):
        assert setup.list_drafts() == []


class TestSubmit:
    def test_submit_writes_profile(self, setup):
        new_profile = {"core": {"name": {"businessFirstName": "Updated"}}}
        setup.submit(new_profile)
        data = setup.load_current()
        assert data["core"]["name"]["businessFirstName"] == "Updated"

    def test_submit_creates_backup(self, setup):
        setup.submit({"core": {}})
        bak_path = setup.profile_path + ".bak"
        assert os.path.exists(bak_path)
        bak_data = json.loads(open(bak_path).read())
        assert bak_data["core"]["name"]["businessFirstName"] == "Test"

    def test_submit_strips_meta(self, setup):
        profile_with_meta = {"core": {}, "_meta": {"draft_id": "xyz"}}
        setup.submit(profile_with_meta)
        data = setup.load_current()
        assert "_meta" not in data

    def test_submit_returns_true(self, setup):
        assert setup.submit({"core": {}}) is True
