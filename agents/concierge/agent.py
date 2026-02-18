"""
Concierge orchestrator agent factory.

Routes user messages to MyCareer or JD Composer specialist agents.
"""

from typing import Any

from langchain_core.tools import tool

from core.llm import get_llm
from core.agent.base import BaseAgent
from core.agent.config import AgentConfig
from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill, Task, TaskResult, TaskState, TaskMessage
from core.middleware.summarization import create_summarization_middleware
from agents.concierge.prompts import CONCIERGE_SYSTEM_PROMPT


def _create_agent_tool(agent: BaseAgent, name: str, description: str):
    """Wrap a specialist agent as a tool for the concierge to call."""

    @tool(name, description=description)
    async def agent_tool(message: str) -> str:
        result = await agent.invoke(message)
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            return getattr(last, "content", str(last))
        return "No response from agent."

    return agent_tool


def create_concierge_agent(
    mycareer_agent: BaseAgent,
    jd_composer_agent: BaseAgent,
    checkpointer=None,
) -> BaseAgent:
    """Create the concierge orchestrator that routes to specialist agents."""
    mycareer_tool = _create_agent_tool(
        mycareer_agent,
        name="mycareer_agent",
        description=(
            "Route to the MyCareer agent for career-related requests: "
            "profile analysis, skill suggestions, profile updates, job matching, "
            "job posting Q&A, drafting/sending messages, and applying for roles."
        ),
    )
    jd_composer_tool = _create_agent_tool(
        jd_composer_agent,
        name="jd_composer_agent",
        description=(
            "Route to the JD Composer agent for job description requests: "
            "creating new JDs, searching similar past JDs, editing JD sections, "
            "and finalizing JDs for posting."
        ),
    )

    config = AgentConfig(
        name="concierge",
        description="AutoChat concierge that routes users to the right specialist agent.",
        llm=get_llm(),
        tools=[mycareer_tool, jd_composer_tool],
        system_prompt=CONCIERGE_SYSTEM_PROMPT,
        middleware=[create_summarization_middleware()],
        checkpointer=checkpointer,
    )
    return BaseAgent(config)


class ConciergeProtocol(AgentProtocol):
    """A2A protocol for the concierge orchestrator."""

    def __init__(self, agent: BaseAgent):
        card = AgentCard(
            name="concierge",
            description="AutoChat concierge -- routes to MyCareer or JD Composer agents",
            skills=[
                AgentSkill(name="routing", description="Route messages to specialist agents", tags=["orchestration"]),
                AgentSkill(name="career_search", description="Career search via MyCareer agent", tags=["career"]),
                AgentSkill(name="jd_creation", description="JD creation via JD Composer agent", tags=["jd"]),
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
