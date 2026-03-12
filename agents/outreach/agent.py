"""
Outreach agent factory.
"""

from core.llm import get_llm
from core.state import BaseContext
from core.agent.base import BaseAgent
from core.agent.config import AgentConfig
from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill, Task, TaskResult, TaskState, TaskMessage
from core.middleware.summarization import create_summarization_middleware
from core.middleware.tool_monitor import tool_monitor_middleware
from agents.shared.middleware import employee_personalization
from agents.outreach.prompts import OUTREACH_SYSTEM_PROMPT, OUTREACH_WELCOME_ADDENDUM
from agents.outreach.tools import OUTREACH_TOOLS


class OutreachContext(BaseContext):
    """Runtime context for Outreach agent."""


def create_outreach_agent(checkpointer=None) -> BaseAgent:
    """Create and return a configured Outreach agent."""
    config = AgentConfig(
        name="outreach",
        description="Helps employees draft and send messages to hiring managers.",
        llm=get_llm(),
        tools=OUTREACH_TOOLS,
        system_prompt=OUTREACH_SYSTEM_PROMPT + OUTREACH_WELCOME_ADDENDUM,
        middleware=[
            create_summarization_middleware(),
            employee_personalization,
            tool_monitor_middleware,
        ],
        context_schema=OutreachContext,
        checkpointer=checkpointer,
        context_factory=lambda thread_id: OutreachContext(thread_id=thread_id),
    )
    return BaseAgent(config)


class OutreachProtocol(AgentProtocol):
    """A2A protocol implementation for Outreach agent."""

    def __init__(self, agent: BaseAgent):
        card = AgentCard(
            name="outreach",
            description="Outreach assistant for employee communication",
            skills=[
                AgentSkill(name="draft_message", description="Draft messages to hiring managers", tags=["messaging", "draft"]),
                AgentSkill(name="send_message", description="Send drafted messages via Teams", tags=["messaging", "send"]),
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
                messages=[TaskMessage(role="agent", content="No user message found in task.")],
            )

        try:
            metadata = dict(task.metadata) if task.metadata else {}
            if "thread_id" not in metadata:
                metadata["thread_id"] = task.id
            context = OutreachContext(**metadata)
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
