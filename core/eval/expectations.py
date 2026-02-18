"""
Expectation checkers for evaluating agent responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExpectationResult:
    passed: bool
    check_name: str
    details: str = ""


def check_tool_called(
    messages: list,
    expected_tool: str,
) -> ExpectationResult:
    """Check that a specific tool was called in the agent response."""
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "tool":
            tool_name = getattr(msg, "name", "")
            if tool_name == expected_tool:
                return ExpectationResult(
                    passed=True,
                    check_name="tool_called",
                    details=f"Tool '{expected_tool}' was called.",
                )
        if hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                if name == expected_tool:
                    return ExpectationResult(
                        passed=True,
                        check_name="tool_called",
                        details=f"Tool '{expected_tool}' was called.",
                    )

    found_tools = []
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "tool":
            found_tools.append(getattr(msg, "name", "unknown"))
        if hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                found_tools.append(name)

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


def check_success(
    messages: list,
) -> ExpectationResult:
    """Check that tool results indicate success."""
    import json

    for msg in messages:
        if hasattr(msg, "type") and msg.type == "tool":
            content = getattr(msg, "content", "")
            try:
                data = json.loads(content) if isinstance(content, str) else content
                if isinstance(data, dict) and data.get("success") is True:
                    return ExpectationResult(
                        passed=True,
                        check_name="success",
                        details="Tool returned success=True",
                    )
            except (json.JSONDecodeError, TypeError):
                continue

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
