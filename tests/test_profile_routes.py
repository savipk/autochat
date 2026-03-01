"""
Tests for profile API routes using FastAPI TestClient.
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.profile_routes import router, _profile_updated_flags

SAMPLE_PROFILE = {
    "core": {
        "name": {"businessFirstName": "Test", "businessLastName": "User"},
        "completionScore": 60,
    }
}


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Create a test FastAPI app with the profile router mounted."""
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(SAMPLE_PROFILE))

    import core.profile_manager
    monkeypatch.setattr(core.profile_manager, "DRAFTS_BASE_DIR", str(tmp_path / "drafts"))

    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def headers(tmp_path):
    return {
        "X-Username": "testuser",
        "X-Profile-Path": str(tmp_path / "profile.json"),
    }


class TestGetCurrentProfile:
    def test_returns_profile(self, client, headers):
        resp = client.get("/api/profile/current", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["core"]["name"]["businessFirstName"] == "Test"


class TestDraftRoutes:
    def test_save_and_list(self, client, headers):
        # Save a draft
        resp = client.post(
            "/api/profile/drafts",
            headers=headers,
            json={"profile_data": SAMPLE_PROFILE, "label": "test-draft"},
        )
        assert resp.status_code == 200
        draft_id = resp.json()["draft_id"]

        # List drafts
        resp = client.get("/api/profile/drafts", headers=headers)
        assert resp.status_code == 200
        drafts = resp.json()
        assert len(drafts) == 1
        assert drafts[0]["id"] == draft_id

    def test_load_draft(self, client, headers):
        resp = client.post(
            "/api/profile/drafts",
            headers=headers,
            json={"profile_data": {"foo": "bar"}, "label": ""},
        )
        draft_id = resp.json()["draft_id"]

        resp = client.get(f"/api/profile/drafts/{draft_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["foo"] == "bar"


class TestSubmit:
    def test_submit_persists(self, client, headers, tmp_path):
        new_profile = {"core": {"name": {"businessFirstName": "Submitted"}}}
        resp = client.post(
            "/api/profile/submit",
            headers=headers,
            json={"profile_data": new_profile},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify on disk
        data = json.loads((tmp_path / "profile.json").read_text())
        assert data["core"]["name"]["businessFirstName"] == "Submitted"


class TestPollUpdate:
    def test_poll_no_update(self, client, headers):
        resp = client.get("/api/profile/poll-update", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["updated"] is False

    def test_poll_with_update(self, client, headers):
        _profile_updated_flags["testuser"] = True
        resp = client.get("/api/profile/poll-update", headers=headers)
        assert resp.json()["updated"] is True
        # Flag should be cleared
        resp = client.get("/api/profile/poll-update", headers=headers)
        assert resp.json()["updated"] is False
