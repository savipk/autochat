"""
BaseAgent wrapping LangChain's create_agent.
"""

from typing import Any, AsyncIterator

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from core.agent.config import AgentConfig


class BaseAgent:
    """Wraps create_agent with a consistent interface for all agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.checkpointer = config.checkpointer or InMemorySaver()
        self._graph = self._build()

    def _build(self):
        kwargs: dict[str, Any] = {
            "model": self.config.llm,
            "tools": self.config.tools,
            "prompt": self.config.system_prompt,
            "name": self.config.name,
            "checkpointer": self.checkpointer,
        }
        if self.config.middleware:
            kwargs["middleware"] = self.config.middleware
        if self.config.state_schema:
            kwargs["state_schema"] = self.config.state_schema
        if self.config.context_schema:
            kwargs["context_schema"] = self.config.context_schema
        return create_agent(**kwargs)

    @property
    def graph(self):
        return self._graph

    async def invoke(
        self,
        message: str,
        *,
        context: Any = None,
        thread_id: str = "",
    ) -> dict:
        config: dict[str, Any] = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}
        kwargs: dict[str, Any] = {
            "input": {"messages": [{"role": "user", "content": message}]},
            "config": config,
        }
        if context is not None:
            kwargs["context"] = context
        return await self._graph.ainvoke(**kwargs)

    async def stream(
        self,
        message: str,
        *,
        context: Any = None,
        thread_id: str = "",
    ) -> AsyncIterator[dict]:
        config: dict[str, Any] = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}
        kwargs: dict[str, Any] = {
            "input": {"messages": [{"role": "user", "content": message}]},
            "config": config,
            "stream_mode": "values",
        }
        if context is not None:
            kwargs["context"] = context
        async for chunk in self._graph.astream(**kwargs):
            yield chunk
