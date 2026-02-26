"""
Shared context base class for all agents.

Agent-specific context classes extend ``BaseContext`` with their own
fields (e.g. ``MyCareerContext.completion_score``).
"""

from pydantic import BaseModel


class BaseContext(BaseModel):
    """Fields common to every agent's runtime context.

    ``thread_id`` identifies the current conversation and is set by
    the Chainlit session or the A2A task metadata.
    """
    thread_id: str = ""


class AppContext(BaseContext):
    """Session-level context for the orchestrator.

    Carries only the minimum state needed for personalized greetings —
    the orchestrator should not hold worker-agent-specific concerns.
    """
    first_name: str = ""
    display_name: str = ""
