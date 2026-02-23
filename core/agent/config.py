"""
Agent configuration dataclass.
"""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AgentConfig:
    """Declarative configuration for an agent."""
    name: str
    description: str
    llm: Any
    tools: list = field(default_factory=list)
    system_prompt: str = ""
    middleware: list = field(default_factory=list)
    state_schema: type | None = None
    context_schema: type | None = None
    checkpointer: Any = None
    context_factory: Callable[[str], Any] | None = None
