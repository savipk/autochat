"""
Evaluation runner -- executes multi-turn scenarios against an agent.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from core.eval.expectations import evaluate_expectations, ExpectationResult

logger = logging.getLogger("chatbot.eval")


@dataclass
class TurnResult:
    turn: int
    user_input: str
    expectations: dict[str, Any]
    checks: list[ExpectationResult] = field(default_factory=list)
    response_text: str = ""
    elapsed_seconds: float = 0.0

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


@dataclass
class ScenarioResult:
    name: str
    turns: list[TurnResult] = field(default_factory=list)
    total_elapsed: float = 0.0

    @property
    def passed(self) -> bool:
        return all(t.passed for t in self.turns)

    @property
    def pass_rate(self) -> float:
        if not self.turns:
            return 0.0
        return sum(1 for t in self.turns if t.passed) / len(self.turns)

    def summary(self) -> str:
        lines = [
            f"Scenario: {self.name}",
            f"Result: {'PASS' if self.passed else 'FAIL'}",
            f"Pass rate: {self.pass_rate:.0%} ({sum(1 for t in self.turns if t.passed)}/{len(self.turns)})",
            f"Total time: {self.total_elapsed:.1f}s",
            "",
        ]
        for t in self.turns:
            status = "PASS" if t.passed else "FAIL"
            lines.append(f"  Turn {t.turn}: [{status}] \"{t.user_input}\" ({t.elapsed_seconds:.1f}s)")
            for c in t.checks:
                check_status = "ok" if c.passed else "FAIL"
                lines.append(f"    - {c.check_name}: {check_status} -- {c.details}")
        return "\n".join(lines)


def load_scenario(path: str) -> dict:
    """Load a scenario JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class EvalRunner:
    """Runs evaluation scenarios against an agent."""

    def __init__(self, agent, profile: dict[str, Any] | None = None):
        self.agent = agent
        self.profile = profile or {}

    async def run_scenario(self, scenario: dict, thread_id: str = "eval") -> ScenarioResult:
        """Execute all turns in a scenario sequentially."""
        scenario_name = scenario.get("name", "unnamed")
        turns = scenario.get("turns", [])

        result = ScenarioResult(name=scenario_name)
        total_start = time.monotonic()

        for turn_data in turns:
            turn_num = turn_data.get("turn", 0)
            user_input = turn_data.get("user", "")
            expectations = turn_data.get("expectations", {})

            logger.info("Turn %d: %s", turn_num, user_input)
            turn_start = time.monotonic()

            try:
                agent_result = await self.agent.invoke(
                    user_input,
                    thread_id=thread_id,
                )
                messages = agent_result.get("messages", [])
            except Exception as e:
                logger.exception("Turn %d failed", turn_num)
                messages = []

            elapsed = time.monotonic() - turn_start

            checks = evaluate_expectations(messages, expectations)

            last_msg = messages[-1] if messages else None
            response_text = getattr(last_msg, "content", str(last_msg)) if last_msg else ""

            turn_result = TurnResult(
                turn=turn_num,
                user_input=user_input,
                expectations=expectations,
                checks=checks,
                response_text=response_text,
                elapsed_seconds=elapsed,
            )
            result.turns.append(turn_result)
            logger.info("Turn %d: %s", turn_num, "PASS" if turn_result.passed else "FAIL")

        result.total_elapsed = time.monotonic() - total_start
        return result

    async def run_scenario_file(self, path: str, thread_id: str = "eval") -> ScenarioResult:
        """Load and run a scenario from a JSON file."""
        scenario = load_scenario(path)
        return await self.run_scenario(scenario, thread_id=thread_id)
