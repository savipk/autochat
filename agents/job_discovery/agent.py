"""
Job Discovery agent factory.
"""

from core.llm import get_llm
from core.state import BaseContext
from core.agent.base import BaseAgent
from core.agent.config import AgentConfig
from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill, Task, TaskResult, TaskState, TaskMessage
from core.middleware.summarization import create_summarization_middleware
from core.middleware.tool_monitor import tool_monitor_middleware
from agents.shared.middleware import employee_personalization, profile_warning_middleware
from agents.job_discovery.prompts import JOB_DISCOVERY_SYSTEM_PROMPT, JOB_DISCOVERY_WELCOME_ADDENDUM
from agents.job_discovery.tools import JOB_DISCOVERY_TOOLS


class JobDiscoveryContext(BaseContext):
    """Runtime context for Job Discovery agent."""


def create_job_discovery_agent(checkpointer=None) -> BaseAgent:
    """Create and return a configured Job Discovery agent."""
    config = AgentConfig(
        name="job_discovery",
        description="Helps employees find matching internal job postings, view job details, and ask questions about job descriptions.",
        llm=get_llm(),
        tools=JOB_DISCOVERY_TOOLS,
        system_prompt=JOB_DISCOVERY_SYSTEM_PROMPT + JOB_DISCOVERY_WELCOME_ADDENDUM,
        middleware=[
            create_summarization_middleware(),
            employee_personalization,
            profile_warning_middleware,
            tool_monitor_middleware,
        ],
        context_schema=JobDiscoveryContext,
        checkpointer=checkpointer,
        context_factory=lambda thread_id: JobDiscoveryContext(thread_id=thread_id),
    )
    return BaseAgent(config)


class JobDiscoveryProtocol(AgentProtocol):
    """A2A protocol implementation for Job Discovery agent."""

    def __init__(self, agent: BaseAgent):
        card = AgentCard(
            name="job_discovery",
            description="Job discovery assistant for employees",
            skills=[
                AgentSkill(name="find_matching_jobs", description="Find internal job postings matching the user's profile", tags=["jobs", "matching"]),
                AgentSkill(name="view_job_details", description="View detailed job posting information", tags=["jobs", "details"]),
                AgentSkill(name="ask_job_question", description="Answer questions about job descriptions", tags=["jobs", "qa"]),
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
            context = JobDiscoveryContext(**metadata)
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
