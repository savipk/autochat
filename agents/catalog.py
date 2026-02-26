"""
Agent catalog — the single place that wires worker agents into the registry.

To add a new agent:
  1. Create agents/<name>/agent.py with a ``create_<name>_agent()`` factory.
  2. Import it here and call ``registry.register(...)``.

No other files need to change.
"""

from core.agent.registry import AgentRegistry
from agents.mycareer.agent import create_mycareer_agent
from agents.jd_generator.agent import create_jd_agent


def build_agent_catalog(checkpointer=None) -> AgentRegistry:
    """Build and return an ``AgentRegistry`` containing all configured agents."""
    registry = AgentRegistry()
    registry.register(create_mycareer_agent(checkpointer=checkpointer))
    registry.register(create_jd_agent(checkpointer=checkpointer))
    return registry
