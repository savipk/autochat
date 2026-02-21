"""
A2A-compatible agent protocol.

Mirrors the Agent-to-Agent (A2A) protocol task lifecycle so that agents
can communicate via structured tasks rather than raw tool calls.
When deployed via LangGraph Server, /a2a/{assistant_id} is auto-exposed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentSkill:
    name: str
    description: str
    tags: list[str] = field(default_factory=list)


@dataclass
class AgentCard:
    """Describes an agent's capabilities -- maps to A2A Agent Card."""
    name: str
    description: str
    skills: list[AgentSkill] = field(default_factory=list)
    url: str | None = None


@dataclass
class TaskMessage:
    role: str  # "user" or "agent"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: TaskState = TaskState.SUBMITTED
    messages: list[TaskMessage] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    task_id: str
    state: TaskState
    messages: list[TaskMessage] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)


class AgentProtocol:
    """
    A2A-compatible protocol interface.
    Each specialist agent implements this to receive tasks from the orchestrator.
    """

    def __init__(self, agent_card: AgentCard) -> None:
        self.agent_card = agent_card
        self._tasks: dict[str, Task] = {}

    async def send_task(self, task: Task) -> TaskResult:
        """Submit a task and get a result. Override in subclasses."""
        self._tasks[task.id] = task
        task.state = TaskState.WORKING
        raise NotImplementedError("Subclasses must implement send_task")

    async def get_task_status(self, task_id: str) -> TaskState:
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")
        return task.state

    async def cancel_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        task.state = TaskState.FAILED
        return True

    def get_agent_card(self) -> dict[str, Any]:
        """Return JSON-serializable agent card for A2A discovery."""
        return {
            "name": self.agent_card.name,
            "description": self.agent_card.description,
            "skills": [
                {"name": s.name, "description": s.description, "tags": s.tags}
                for s in self.agent_card.skills
            ],
            "url": self.agent_card.url,
        }
