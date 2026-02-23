"""
Expectation checkers for evaluating agent responses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

_ORCHESTRATOR_TOOL_NAMES = {"mycareer_agent", "jd_generator_agent"}


@dataclass
class ExpectationResult:
    passed: bool
    check_name: str
    details: str = ""


def _iter_tool_names(messages: list) -> list[str]:
    """Collect all tool names from messages, unwrapping orchestrator agent tools."""
    names: list[str] = []
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "tool":
            tool_name = getattr(msg, "name", "")
            if tool_name in _ORCHESTRATOR_TOOL_NAMES:
                try:
                    content = msg.content
                    parsed = json.loads(content) if isinstance(content, str) else content
                except (json.JSONDecodeError, TypeError):
                    parsed = {}
                if isinstance(parsed, dict) and "tool_calls" in parsed:
                    for inner in parsed["tool_calls"]:
                        names.append(inner.get("name", ""))
                    continue
            names.append(tool_name)
        if hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                names.append(name)
    return names


def check_tool_called(
    messages: list,
    expected_tool: str,
) -> ExpectationResult:
    """Check that a specific tool was called in the agent response."""
    found_tools = _iter_tool_names(messages)

    if expected_tool in found_tools:
        return ExpectationResult(
            passed=True,
            check_name="tool_called",
            details=f"Tool '{expected_tool}' was called.",
        )

    return ExpectationResult(
        passed=False,
        check_name="tool_called",
        details=f"Expected '{expected_tool}', found tools: {found_tools}",
    )


def check_response_contains(
    messages: list,
    expected_strings: list[str],
) -> ExpectationResult:
    """Check that the final response contains expected strings."""
    full_text = ""
    for msg in messages:
        content = getattr(msg, "content", "")
        if isinstance(content, str):
            full_text += " " + content

    full_text_lower = full_text.lower()
    missing = [s for s in expected_strings if s.lower() not in full_text_lower]

    if not missing:
        return ExpectationResult(
            passed=True,
            check_name="response_contains",
            details=f"All expected strings found: {expected_strings}",
        )
    return ExpectationResult(
        passed=False,
        check_name="response_contains",
        details=f"Missing strings: {missing}",
    )


def _iter_tool_results(messages: list) -> list[dict]:
    """Collect all parsed tool result dicts, unwrapping orchestrator agent tools."""
    results: list[dict] = []
    for msg in messages:
        if not (hasattr(msg, "type") and msg.type == "tool"):
            continue
        tool_name = getattr(msg, "name", "")
        try:
            content = msg.content
            data = json.loads(content) if isinstance(content, str) else content
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(data, dict):
            continue

        if tool_name in _ORCHESTRATOR_TOOL_NAMES and "tool_calls" in data:
            for inner in data["tool_calls"]:
                inner_content = inner.get("content", {})
                if isinstance(inner_content, str):
                    try:
                        inner_content = json.loads(inner_content)
                    except (json.JSONDecodeError, TypeError):
                        continue
                if isinstance(inner_content, dict):
                    results.append(inner_content)
        else:
            results.append(data)
    return results


def check_success(
    messages: list,
) -> ExpectationResult:
    """Check that tool results indicate success."""
    for data in _iter_tool_results(messages):
        if data.get("success") is True:
            return ExpectationResult(
                passed=True,
                check_name="success",
                details="Tool returned success=True",
            )

    return ExpectationResult(
        passed=False,
        check_name="success",
        details="No tool result with success=True found",
    )


def evaluate_expectations(
    messages: list,
    expectations: dict[str, Any],
) -> list[ExpectationResult]:
    """Run all expectation checks for a turn."""
    results = []

    if "tool_called" in expectations:
        results.append(check_tool_called(messages, expectations["tool_called"]))

    if "response_contains" in expectations:
        results.append(check_response_contains(messages, expectations["response_contains"]))

    if expectations.get("success"):
        results.append(check_success(messages))

    return results
