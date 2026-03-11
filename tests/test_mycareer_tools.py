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

WELL_STRUCTURED_PROFILE = {
    "core": {
        "name": {"businessFirstName": "Test", "businessLastName": "User"},
        "experience": {"experiences": [{"id": "e1", "jobTitle": "Engineer", "company": "Acme", "startDate": "2020-01-01"}]},
        "qualification": {"educations": [{"id": "q1", "institutionName": "MIT", "degree": "BS CS"}]},
        "skills": {"top": [{"id": "s1", "name": "Python", "source": "AI_INFERRED"}], "additional": [{"id": "s2", "name": "Docker", "source": "MANUAL"}]},
        "careerAspirationPreference": {"preferredAspirations": [{"code": "x", "description": "Leadership"}]},
        "careerLocationPreference": {"preferredRelocationRegions": [{"code": "US", "description": "United States"}]},
        "careerRolePreference": {"preferredRoles": [{"code": "dev", "description": "Developer"}]},
        "language": {"languages": [{"id": "l1", "language": {"code": "en", "description": "English"}, "proficiency": {"code": "FLUENT", "description": "Fluent"}}]},
    }
}


@pytest.fixture
def empty_profile_path(tmp_path, monkeypatch):
    """Write an empty-ish profile to a temp file and point PROFILE_PATH at it."""
    path = tmp_path / "empty_profile.json"
    path.write_text(json.dumps(EMPTY_PROFILE))
    import core.profile
    monkeypatch.setattr(core.profile, "PROFILE_PATH", str(path))
    return str(path)


@pytest.fixture
def full_profile_path(tmp_path, monkeypatch):
    """Write a well-structured full profile and point PROFILE_PATH at it."""
    path = tmp_path / "full_profile.json"
    path.write_text(json.dumps(WELL_STRUCTURED_PROFILE))
    import core.profile
    monkeypatch.setattr(core.profile, "PROFILE_PATH", str(path))
    return str(path)


@pytest.fixture
def mock_user_context(tmp_path, monkeypatch):
    """Mock user context + write a profile so update_profile can persist."""
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(WELL_STRUCTURED_PROFILE))
    import core.profile
    monkeypatch.setattr(core.profile, "PROFILE_PATH", str(path))

    import agents.shared.tools.update_profile  # noqa: F401
    umod = sys.modules["agents.shared.tools.update_profile"]
    monkeypatch.setattr(umod, "_get_user_context", lambda: ("testuser", str(path)))

    import core.profile_manager
    monkeypatch.setattr(core.profile_manager, "DRAFTS_BASE_DIR", str(tmp_path / "drafts"))
    return str(path)


class TestProfileAnalyzer:
    def _run(self, **kwargs):
        from agents.shared.tools.profile_analyzer import run_profile_analyzer
        return run_profile_analyzer(**kwargs)

    def test_full_profile_scores_high(self, full_profile_path):
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
        from agents.shared.tools.update_profile import run_update_profile
        return run_update_profile(**kwargs)

    def test_update_skills_default(self, mock_user_context):
        result = self._run()
        assert result["success"] is True
        assert result["section"] == "skills"
        assert "A2A" in result["updated_fields"]["topSkills"]

    def test_unsupported_section(self, mock_user_context):
        result = self._run(section="bogus_section")
        assert result["success"] is False
        assert "not yet supported" in result["error"]

    def test_experience_section_supported(self, mock_user_context):
        updates = {"experiences": [{"jobTitle": "Engineer", "company": "Acme"}]}
        result = self._run(section="experience", updates=updates)
        assert result["success"] is True
        assert result["section"] == "experience"

    def test_language_section_supported(self, mock_user_context):
        updates = {"languages": [{"language": {"description": "German"}, "proficiency": {"description": "Native"}}]}
        result = self._run(section="language", updates=updates)
        assert result["success"] is True
        assert result["section"] == "language"

    def test_update_skills_with_specific_list(self, mock_user_context):
        skills = ["Python", "Docker", "Kubernetes", "Terraform", "Go"]
        result = self._run(updates={"skills": skills})
        assert result["success"] is True
        assert result["updated_fields"]["topSkills"] == ["Python", "Docker", "Kubernetes"]
        assert result["updated_fields"]["additionalSkills"] == ["Terraform", "Go"]

    def test_update_skills_with_empty_list(self, mock_user_context):
        result = self._run(updates={"skills": []})
        assert result["success"] is True
        assert result["updated_fields"]["topSkills"] == []
        assert result["updated_fields"]["additionalSkills"] == []


class TestInferSkills:
    def _run(self, **kwargs):
        from agents.shared.tools.infer_skills import run_infer_skills
        return run_infer_skills(**kwargs)

    def test_returns_skills(self):
        result = self._run()
        assert result["success"] is True
        assert "A2A" in result["topSkills"]
        assert "MCP" in result["topSkills"]
        assert "RAG" in result["topSkills"]
        assert len(result["additionalSkills"]) > 0

    def test_returns_evidence(self):
        result = self._run()
        assert isinstance(result["evidence"], list)
        assert len(result["evidence"]) > 0
        for entry in result["evidence"]:
            assert "skill" in entry
            assert "source" in entry
            assert "detail" in entry

    def test_returns_confidence(self):
        result = self._run()
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1


class TestGetMatches:
    def _run(self, **kwargs):
        from agents.shared.tools.get_matches import run_get_matches
        return run_get_matches(**kwargs)

    def setup_method(self):
        from agents.shared.tools.get_matches import _reset_seen_jobs
        _reset_seen_jobs()

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

    def test_sorted_by_match_score_descending(self):
        result = self._run(top_k=15)
        scores = [m["matchScore"] for m in result["matches"]]
        assert scores == sorted(scores, reverse=True)

    # --- Filter tests ---

    def test_filter_by_country(self):
        result = self._run(filters={"country": "India"})
        assert result["success"] is True
        assert result["count"] > 0
        for m in result["matches"]:
            assert "india" in m["country"].lower()

    def test_filter_by_location(self):
        result = self._run(filters={"location": "London"}, top_k=10)
        assert result["success"] is True
        assert result["count"] > 0
        for m in result["matches"]:
            assert "london" in m["location"].lower()

    def test_filter_by_level(self):
        result = self._run(filters={"level": "DIR"}, top_k=10)
        assert result["success"] is True
        assert result["count"] > 0
        for m in result["matches"]:
            assert m["corporateTitleCode"] == "DIR"

    def test_filter_by_level_case_insensitive(self):
        result = self._run(filters={"level": "dir"}, top_k=10)
        assert result["count"] > 0
        for m in result["matches"]:
            assert m["corporateTitleCode"] == "DIR"

    def test_filter_by_orgline(self):
        result = self._run(filters={"orgLine": "Risk & Compliance"}, top_k=10)
        assert result["success"] is True
        assert result["count"] > 0
        for m in result["matches"]:
            assert "risk & compliance" in m["orgLine"].lower()

    def test_filter_by_department_alias(self):
        result = self._run(filters={"department": "Investment Banking"}, top_k=10)
        assert result["count"] > 0
        for m in result["matches"]:
            assert "investment banking" in m["orgLine"].lower()

    def test_filter_by_skills(self):
        result = self._run(filters={"skills": ["Python"]}, top_k=10)
        assert result["success"] is True
        assert result["count"] > 0
        for m in result["matches"]:
            assert any("python" in s.lower() for s in m["matchingSkills"])

    def test_filter_by_min_score(self):
        result = self._run(filters={"minScore": 2.5}, top_k=15)
        assert result["success"] is True
        for m in result["matches"]:
            assert m["matchScore"] >= 2.5

    def test_combined_filters(self):
        result = self._run(filters={"country": "United Kingdom", "level": "ED"}, top_k=10)
        assert result["success"] is True
        for m in result["matches"]:
            assert "united kingdom" in m["country"].lower()
            assert m["corporateTitleCode"] == "ED"

    def test_filter_zero_results(self):
        result = self._run(filters={"country": "Antarctica"})
        assert result["success"] is True
        assert result["count"] == 0
        assert result["total_available"] == 0
        assert result["matches"] == []

    def test_unknown_filter_key_ignored(self):
        result = self._run(filters={"nonexistent_key": "value"})
        assert result["success"] is True
        assert result["count"] > 0

    # --- Search tests ---

    def test_search_single_term(self):
        result = self._run(search_text="GenAI", top_k=10)
        assert result["success"] is True
        assert result["count"] >= 1

    def test_search_multi_term(self):
        result = self._run(search_text="data engineering", top_k=10)
        assert result["success"] is True
        assert result["count"] >= 1

    def test_search_case_insensitive(self):
        result = self._run(search_text="GENAI", top_k=10)
        assert result["count"] >= 1

    def test_search_in_requirements(self):
        result = self._run(search_text="Kubernetes certification", top_k=10)
        assert result["count"] >= 1

    def test_search_zero_results(self):
        result = self._run(search_text="xyznonexistent12345")
        assert result["success"] is True
        assert result["count"] == 0

    def test_search_combined_with_filter(self):
        result = self._run(filters={"country": "United Kingdom"}, search_text="platform", top_k=10)
        assert result["success"] is True
        for m in result["matches"]:
            assert "united kingdom" in m["country"].lower()

    # --- Pagination tests ---

    def test_pagination_offset(self):
        all_results = self._run(top_k=15)
        page1 = self._run(top_k=3, offset=0)
        page2 = self._run(top_k=3, offset=3)
        assert page1["matches"][0]["id"] != page2["matches"][0]["id"]
        assert page1["total_available"] == page2["total_available"]

    def test_pagination_has_more(self):
        result = self._run(top_k=3, offset=0)
        assert result["has_more"] is True
        assert result["total_available"] > 3

    def test_pagination_last_page(self):
        total = self._run(top_k=100)["total_available"]
        result = self._run(top_k=100, offset=0)
        assert result["has_more"] is False

    def test_pagination_total_available(self):
        result = self._run(top_k=3)
        assert result["total_available"] >= result["count"]

    # --- isNewToUser tests ---

    def test_is_new_to_user_first_call(self):
        result = self._run(thread_id="test_thread_1")
        for m in result["matches"]:
            assert m["isNewToUser"] is True

    def test_is_new_to_user_second_call(self):
        result1 = self._run(thread_id="test_thread_2")
        first_ids = {m["id"] for m in result1["matches"]}
        result2 = self._run(thread_id="test_thread_2")
        for m in result2["matches"]:
            if m["id"] in first_ids:
                assert m["isNewToUser"] is False

    def test_is_new_to_user_different_threads(self):
        self._run(thread_id="thread_a")
        result = self._run(thread_id="thread_b")
        for m in result["matches"]:
            assert m["isNewToUser"] is True

    # --- Profile summary ---

    def test_profile_summary_present(self):
        result = self._run()
        assert "profile_summary" in result
        assert "name" in result["profile_summary"]
        assert "topSkills" in result["profile_summary"]
        assert "completionScore" in result["profile_summary"]

    # --- Response fields ---

    def test_response_contains_pagination_fields(self):
        result = self._run()
        assert "total_available" in result
        assert "offset" in result
        assert "has_more" in result


class TestAskJdQa:
    def _run(self, *args, **kwargs):
        from agents.shared.tools.ask_jd_qa import run_ask_jd_qa
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
        from agents.shared.tools.draft_message import run_draft_message
        return run_draft_message(**kwargs)

    def test_draft_with_profile(self):
        result = self._run()
        assert result["success"] is True
        assert result["recipient_name"] == "Prasanth Jagannathan"
        assert result["message_type"] == "teams"
        assert len(result["message_body"]) > 0


class TestSendMessage:
    def _run(self, *args, **kwargs):
        from agents.shared.tools.send_message import run_send_message
        return run_send_message(*args, **kwargs)

    def test_send_success(self):
        result = self._run("Prasanth Jagannathan", "Hello!", "teams")
        assert result["success"] is True
        assert result["recipient_name"] == "Prasanth Jagannathan"
        assert "sent_at" in result


class TestApplyForRole:
    def _run(self, **kwargs):
        from agents.shared.tools.apply_for_role import run_apply_for_role
        return run_apply_for_role(**kwargs)

    def test_apply_success(self):
        result = self._run(job_id="331525BR")
        assert result["success"] is True
        assert result["job_id"] == "331525BR"
        assert result["status"] == "submitted"
        assert "application_id" in result
