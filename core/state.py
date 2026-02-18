"""
Base agent state definitions.
"""

from typing import Any
from typing_extensions import TypedDict
from pydantic import BaseModel


class BaseAgentState(TypedDict, total=False):
    """Base state shared by all agents. Extended by each agent as needed."""
    messages: list
    current_agent: str


class UserContext(BaseModel):
    """Runtime context passed to agents (not persisted in state)."""
    profile: dict[str, Any] = {}
    completion_score: int = 100
    thread_id: str = ""
    user_name: str = ""
