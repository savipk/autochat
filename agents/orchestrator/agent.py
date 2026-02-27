"""
Orchestrator agent factory.

Routes user messages to specialist agents discovered via ``AgentRegistry``.
Context is threaded from app.py through the orchestrator down to each
specialist via a factory-scoped ContextVar so there is no global state.
"""

from __future__ import annotations

import contextvars
import json
import logging
from typing import Any

from langchain_core.tools import tool

from core.llm import get_llm
from core.state import AppContext, BaseContext
from core.agent.base import BaseAgent
from core.agent.config import AgentConfig
from core.agent.registry import AgentRegistry
from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill, Task, TaskResult, TaskState, TaskMessage
from core.middleware.summarization import create_summarization_middleware
from core.middleware.tool_monitor import tool_monitor_middleware
from agents.orchestrator.middleware import orchestrator_personalization
from agents.orchestrator.prompts import ORCHESTRATOR_SYSTEM_PROMPT

logger = logging.getLogger("chatbot.orchestrator")


def _create_worker_agent(agent: BaseAgent, name: str, description: str, context_var: contextvars.ContextVar):
    """Wrap a specialist agent as a worker agent for the orchestrator to call.

    Reads the parent ``AppContext`` from *context_var*, builds a
    namespaced ``thread_id``, and constructs the correct worker agent context
    via ``agent.config.context_factory`` (falling back to ``BaseContext``).
    """

    @tool(name, description=description)
    async def worker_agent(message: str) -> str:
        app_ctx = context_var.get()
        parent_thread_id = getattr(app_ctx, "thread_id", "") if app_ctx else ""
        namespaced_id = f"{parent_thread_id}:{name}" if parent_thread_id else ""

        if agent.config.context_factory:
            sub_ctx = agent.config.context_factory(namespaced_id)
        else:
            sub_ctx = BaseContext(thread_id=namespaced_id)

        try:
            result = await agent.invoke(message, context=sub_ctx)
        except Exception as e:
            logger.exception("Worker agent '%s' raised an error", name)
            return json.dumps({
                "response": f"Sorry, the {name} agent encountered an error: {type(e).__name__}. Please try again.",
                "tool_calls": [],
            })

        messages = result.get("messages", [])

        # Slice to current turn only — the checkpointer loads the full
        # history so we must skip tool messages from prior turns.
        turn_start = 0
        for i, msg in enumerate(messages):
            if hasattr(msg, "type") and msg.type == "human":
                turn_start = i
        current_turn_messages = messages[turn_start:]

        inner_tool_calls = []
        for msg in current_turn_messages:
            if hasattr(msg, "type") and msg.type == "tool":
                raw = msg.content
                try:
                    parsed = json.loads(raw) if isinstance(raw, str) else raw
                except (json.JSONDecodeError, TypeError):
                    parsed = raw
                inner_tool_calls.append({
                    "name": getattr(msg, "name", ""),
                    "content": parsed,
                })

        response = ""
        if messages:
            last = messages[-1]
            response = getattr(last, "content", str(last))

        return json.dumps({
            "response": response,
            "tool_calls": inner_tool_calls,
        })

    return worker_agent


class OrchestratorAgent(BaseAgent):
    """Orchestrator that stashes runtime context before invoking the graph
    so that worker agent wrappers can pick it up.
    """

    def __init__(self, config: AgentConfig, context_var: contextvars.ContextVar) -> None:
        self._context_var = context_var
        super().__init__(config)

    async def invoke(self, message: str, *, context: Any = None) -> dict:
        token = self._context_var.set(context)
        try:
            return await super().invoke(message, context=context)
        finally:
            self._context_var.reset(token)


def create_orchestrator_agent(
    registry: AgentRegistry,
    checkpointer=None,
) -> OrchestratorAgent:
    """Create the orchestrator that routes to specialist agents in *registry*."""
    context_var: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
        "_orchestrator_ctx", default=None
    )

    worker_agents = []
    for agent_name in registry.list_agents():
        agent = registry.get(agent_name)
        worker_agents.append(
            _create_worker_agent(
                agent,
                name=agent_name,
                description=agent.config.description,
                context_var=context_var,
            )
        )

    config = AgentConfig(
        name="orchestrator",
        description="Chat orchestrator that routes users to the right specialist agent.",
        llm=get_llm(),
        tools=worker_agents,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        middleware=[
            create_summarization_middleware(),
            orchestrator_personalization,
            tool_monitor_middleware,
        ],
        context_schema=AppContext,
        checkpointer=checkpointer,
    )
    return OrchestratorAgent(config, context_var)


class OrchestratorProtocol(AgentProtocol):
    """A2A protocol for the orchestrator."""

    def __init__(self, agent: OrchestratorAgent):
        card = AgentCard(
            name="orchestrator",
            description="Chat orchestrator -- routes to MyCareer or JD Generator agents",
            skills=[
                AgentSkill(name="routing", description="Route messages to specialist agents", tags=["orchestration"]),
                AgentSkill(name="career_search", description="Career search via MyCareer agent", tags=["career"]),
                AgentSkill(name="jd_creation", description="JD creation via JD Generator agent", tags=["jd"]),
            ],
        )
        super().__init__(card)
        self._agent = agent

    async def send_task(self, task: Task) -> TaskResult:
        self._tasks[task.id] = task
        task.state = TaskState.WORKING

        user_message = ""
        for msg in reversed(task.messages):
            if msg.role == "user":
                user_message = msg.content
                break

        if not user_message:
            task.state = TaskState.FAILED
            return TaskResult(
                task_id=task.id,
                state=TaskState.FAILED,
                messages=[TaskMessage(role="agent", content="No user message found.")],
            )

        try:
            thread_id_val = task.metadata.get("thread_id", task.id) if task.metadata else task.id
            context = AppContext(thread_id=thread_id_val)
            result = await self._agent.invoke(user_message, context=context)
            response_messages = result.get("messages", [])
            last_msg = response_messages[-1] if response_messages else None
            content = getattr(last_msg, "content", str(last_msg)) if last_msg else "No response"

            task.state = TaskState.COMPLETED
            return TaskResult(
                task_id=task.id,
                state=TaskState.COMPLETED,
                messages=[TaskMessage(role="agent", content=content)],
            )
        except Exception as e:
            task.state = TaskState.FAILED
            return TaskResult(
                task_id=task.id,
                state=TaskState.FAILED,
                messages=[TaskMessage(role="agent", content=f"Error: {e}")],
            )
