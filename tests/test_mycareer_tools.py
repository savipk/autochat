"""
Tests for MyCareer tool implementations.
Verifies that the tool logic copied from tpchat works correctly.
These tests import run_* functions directly to avoid langchain_core segfault in CI.
"""

import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

EMPTY_PROFILE = {"core": {"name": {"businessFirstName": "Test", "businessLastName": "User"}}}


@pytest.fixture
def empty_profile_path(tmp_path, monkeypatch):
    """Write an empty-ish profile to a temp file and point PROFILE_PATH at it."""
    path = tmp_path / "empty_profile.json"
    path.write_text(json.dumps(EMPTY_PROFILE))
    import core.profile
    monkeypatch.setattr(core.profile, "PROFILE_PATH", str(path))
    return str(path)


class TestProfileAnalyzer:
    def _run(self, **kwargs):
        from agents.mycareer.tools.profile_analyzer import run_profile_analyzer
        return run_profile_analyzer(**kwargs)

    def test_full_profile_scores_high(self):
        result = self._run()
        assert result["success"] is True
        assert result["completionScore"] >= 80
        assert isinstance(result["sectionScores"], dict)

    def test_empty_profile_scores_low(self, empty_profile_path):
        result = self._run()
        assert result["success"] is True
        assert result["completionScore"] < 50
        assert len(result["missingSections"]) > 0

    def test_missing_sections_identified(self, empty_profile_path):
        result = self._run()
        assert "skills" in result["missingSections"]
        assert "experience" in result["missingSections"]


class TestUpdateProfile:
    def _run(self, **kwargs):
        from agents.mycareer.tools.update_profile import run_update_profile
        return run_update_profile(**kwargs)

    def test_update_skills_default(self):
        result = self._run()
        assert result["success"] is True
        assert result["section"] == "skills"
        assert "A2A" in result["updated_fields"]["topSkills"]

    def test_unsupported_section(self):
        result = self._run(section="experience")
        assert result["success"] is False
        assert "not yet supported" in result["error"]


class TestInferSkills:
    def _run(self, **kwargs):
        from agents.mycareer.tools.infer_skills import run_infer_skills
        return run_infer_skills(**kwargs)

    def test_returns_skills(self):
        result = self._run()
        assert result["success"] is True
        assert "A2A" in result["topSkills"]
        assert "MCP" in result["topSkills"]
        assert "RAG" in result["topSkills"]
        assert len(result["additionalSkills"]) > 0


class TestGetMatches:
    def _run(self, **kwargs):
        from agents.mycareer.tools.get_matches import run_get_matches
        return run_get_matches(**kwargs)

    def test_returns_matches(self):
        result = self._run()
        assert result["success"] is True
        assert result["count"] > 0
        assert len(result["matches"]) <= 3

    def test_match_has_required_fields(self):
        result = self._run()
        for match in result["matches"]:
            assert "title" in match
            assert "id" in match
            assert "daysAgo" in match


class TestAskJdQa:
    def _run(self, *args, **kwargs):
        from agents.mycareer.tools.ask_jd_qa import run_ask_jd_qa
        return run_ask_jd_qa(*args, **kwargs)

    def test_team_size_question(self):
        result = self._run("331525BR", "What is the team size?")
        assert result["success"] is True
        assert result["answer_found"] is True
        assert "10-15" in result["answer"]

    def test_project_focus_question(self):
        result = self._run("331525BR", "Which project is the role focused on?")
        assert result["success"] is True
        assert result["answer_found"] is False
        assert result.get("suggest_contact_hiring_manager") is True

    def test_generic_question(self):
        result = self._run("331525BR", "Tell me about this role")
        assert result["success"] is True
        assert result["answer_found"] is True


class TestDraftMessage:
    def _run(self, **kwargs):
        from agents.mycareer.tools.draft_message import run_draft_message
        return run_draft_message(**kwargs)

    def test_draft_with_profile(self):
        result = self._run()
        assert result["success"] is True
        assert result["recipient_name"] == "Prasanth Jagannathan"
        assert result["message_type"] == "teams"
        assert len(result["message_body"]) > 0


class TestSendMessage:
    def _run(self, *args, **kwargs):
        from agents.mycareer.tools.send_message import run_send_message
        return run_send_message(*args, **kwargs)

    def test_send_success(self):
        result = self._run("Prasanth Jagannathan", "Hello!", "teams")
        assert result["success"] is True
        assert result["recipient_name"] == "Prasanth Jagannathan"
        assert "sent_at" in result


class TestApplyForRole:
    def _run(self, **kwargs):
        from agents.mycareer.tools.apply_for_role import run_apply_for_role
        return run_apply_for_role(**kwargs)

    def test_apply_success(self):
        result = self._run(job_id="331525BR")
        assert result["success"] is True
        assert result["job_id"] == "331525BR"
        assert result["status"] == "submitted"
        assert "application_id" in result
