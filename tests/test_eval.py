"""
Tests for the evaluation harness.
"""

import os
import pytest

from core.eval.runner import load_scenario, EvalRunner, ScenarioResult
from core.eval.expectations import (
    check_tool_called,
    check_response_contains,
    check_success,
    evaluate_expectations,
    ExpectationResult,
)


class MockMessage:
    def __init__(self, content="", msg_type="ai", name="", tool_calls=None):
        self.content = content
        self.type = msg_type
        self.name = name
        self.tool_calls = tool_calls or []


class TestExpectations:
    def test_check_tool_called_pass(self):
        messages = [
            MockMessage(msg_type="ai", tool_calls=[{"name": "get_matches"}]),
            MockMessage(content='{"success": true}', msg_type="tool", name="get_matches"),
        ]
        result = check_tool_called(messages, "get_matches")
        assert result.passed is True

    def test_check_tool_called_fail(self):
        messages = [
            MockMessage(msg_type="ai", tool_calls=[{"name": "infer_skills"}]),
        ]
        result = check_tool_called(messages, "get_matches")
        assert result.passed is False

    def test_check_response_contains_pass(self):
        messages = [
            MockMessage(content="Found 3 GenAI Lead roles with A2A skills"),
        ]
        result = check_response_contains(messages, ["GenAI Lead", "A2A"])
        assert result.passed is True

    def test_check_response_contains_fail(self):
        messages = [
            MockMessage(content="Hello there!"),
        ]
        result = check_response_contains(messages, ["GenAI Lead"])
        assert result.passed is False
        assert "GenAI Lead" in result.details

    def test_check_success_pass(self):
        messages = [
            MockMessage(content='{"success": true, "count": 3}', msg_type="tool", name="get_matches"),
        ]
        result = check_success(messages)
        assert result.passed is True

    def test_check_success_fail(self):
        messages = [
            MockMessage(content='{"success": false}', msg_type="tool", name="get_matches"),
        ]
        result = check_success(messages)
        assert result.passed is False

    def test_evaluate_expectations_combined(self):
        messages = [
            MockMessage(msg_type="ai", tool_calls=[{"name": "infer_skills"}]),
            MockMessage(content='{"success": true, "topSkills": ["A2A", "MCP", "RAG"]}', msg_type="tool", name="infer_skills"),
            MockMessage(content="Here are your suggested skills: A2A, MCP, RAG"),
        ]
        expectations = {
            "tool_called": "infer_skills",
            "response_contains": ["A2A", "MCP", "RAG"],
            "success": True,
        }
        results = evaluate_expectations(messages, expectations)
        assert len(results) == 3
        assert all(r.passed for r in results)


class TestLoadScenario:
    def test_load_happy_flow(self):
        path = os.path.join(
            os.path.dirname(__file__), "..", "eval", "scenarios", "mycareer_happy_flow.json"
        )
        scenario = load_scenario(path)
        assert scenario["name"] == "mycareer_happy_flow"
        assert len(scenario["turns"]) == 8
        assert scenario["turns"][0]["user"] == "Suggest skills"
        assert scenario["turns"][0]["expectations"]["tool_called"] == "infer_skills"


class TestScenarioResult:
    def test_all_pass(self):
        from core.eval.runner import TurnResult
        result = ScenarioResult(
            name="test",
            turns=[
                TurnResult(
                    turn=1,
                    user_input="test",
                    expectations={},
                    checks=[ExpectationResult(passed=True, check_name="test")],
                ),
            ],
        )
        assert result.passed is True
        assert result.pass_rate == 1.0

    def test_partial_fail(self):
        from core.eval.runner import TurnResult
        result = ScenarioResult(
            name="test",
            turns=[
                TurnResult(
                    turn=1,
                    user_input="a",
                    expectations={},
                    checks=[ExpectationResult(passed=True, check_name="t")],
                ),
                TurnResult(
                    turn=2,
                    user_input="b",
                    expectations={},
                    checks=[ExpectationResult(passed=False, check_name="t")],
                ),
            ],
        )
        assert result.passed is False
        assert result.pass_rate == 0.5

    def test_summary_output(self):
        from core.eval.runner import TurnResult
        result = ScenarioResult(
            name="test_scenario",
            turns=[
                TurnResult(
                    turn=1,
                    user_input="hello",
                    expectations={},
                    checks=[ExpectationResult(passed=True, check_name="check1", details="ok")],
                    elapsed_seconds=0.5,
                ),
            ],
            total_elapsed=0.5,
        )
        summary = result.summary()
        assert "test_scenario" in summary
        assert "PASS" in summary
