"""
Orchestrator agent factory.

Routes user messages to MyCareer or JD Generator specialist agents.
Context (profile, completion_score, etc.) is threaded from app.py through
the orchestrator down to each specialist via a module-level context holder.
"""

from __future__ import annotations

import contextvars
import logging
from typing import Any

from langchain_core.tools import tool

from core.llm import get_llm
from core.agent.base import BaseAgent
from core.agent.config import AgentConfig
from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill, Task, TaskResult, TaskState, TaskMessage
from core.middleware.summarization import create_summarization_middleware
from agents.orchestrator.prompts import ORCHESTRATOR_SYSTEM_PROMPT

logger = logging.getLogger("chatbot.orchestrator")

_current_context: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
    "_current_context", default=None
)


def _create_agent_tool(agent: BaseAgent, name: str, description: str):
    """Wrap a specialist agent as a tool for the orchestrator to call.

    The tool forwards the active runtime context (set by
    ``OrchestratorAgent.invoke``) so that specialist middleware
    (personalization, profile warnings) receives profile data.
    """

    @tool(name, description=description)
    async def agent_tool(message: str) -> str:
        ctx = _current_context.get()
        try:
            result = await agent.invoke(message, context=ctx)
        except Exception as e:
            logger.exception("Sub-agent '%s' raised an error", name)
            return f"Sorry, the {name} agent encountered an error: {type(e).__name__}. Please try again."
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            return getattr(last, "content", str(last))
        return "No response from agent."

    return agent_tool


class OrchestratorAgent(BaseAgent):
    """Orchestrator that stashes runtime context before invoking the graph
    so that specialist-agent tool wrappers can pick it up.
    """

    async def invoke(self, message: str, *, context: Any = None, thread_id: str = "") -> dict:
        token = _current_context.set(context)
        try:
            return await super().invoke(message, context=context, thread_id=thread_id)
        finally:
            _current_context.reset(token)


def create_orchestrator_agent(
    mycareer_agent: BaseAgent,
    jd_generator_agent: BaseAgent,
    checkpointer=None,
) -> OrchestratorAgent:
    """Create the orchestrator that routes to specialist agents."""
    mycareer_tool = _create_agent_tool(
        mycareer_agent,
        name="mycareer_agent",
        description=(
            "Route to the MyCareer agent for career-related requests: "
            "profile analysis, skill suggestions, profile updates, job matching, "
            "job posting Q&A, drafting/sending messages, and applying for roles."
        ),
    )
    jd_generator_tool = _create_agent_tool(
        jd_generator_agent,
        name="jd_generator_agent",
        description=(
            "Route to the JD Generator agent for job description requests: "
            "creating new JDs, searching similar past JDs, editing JD sections, "
            "and finalizing JDs for posting."
        ),
    )

    config = AgentConfig(
        name="orchestrator",
        description="Chat orchestrator that routes users to the right specialist agent.",
        llm=get_llm(),
        tools=[mycareer_tool, jd_generator_tool],
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        middleware=[create_summarization_middleware()],
        checkpointer=checkpointer,
    )
    return OrchestratorAgent(config)


class OrchestratorProtocol(AgentProtocol):
    """A2A protocol for the orchestrator."""

    def __init__(self, agent: BaseAgent):
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
            result = await self._agent.invoke(
                user_message,
                thread_id=task.metadata.get("thread_id", task.id),
            )
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
