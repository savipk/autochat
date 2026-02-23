"""
MyCareer agent factory.
"""

from core.llm import get_llm
from core.state import BaseContext
from core.agent.base import BaseAgent
from core.agent.config import AgentConfig
from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill, Task, TaskResult, TaskState, TaskMessage
from core.middleware.summarization import create_summarization_middleware
from core.middleware.tool_monitor import tool_monitor_middleware
from agents.mycareer.middleware import first_touch_profile_middleware, mycareer_personalization, profile_warning_middleware
from agents.mycareer.prompts import MYCAREER_SYSTEM_PROMPT, MYCAREER_WELCOME_ADDENDUM
from agents.mycareer.tools import ALL_TOOLS


class MyCareerContext(BaseContext):
    """Runtime context for MyCareer agent."""
    completion_score: int = 100


def create_mycareer_agent(checkpointer=None) -> BaseAgent:
    """Create and return a configured MyCareer agent."""
    config = AgentConfig(
        name="mycareer",
        description="Internal career management assistant that helps employees find jobs, improve profiles, and connect with hiring managers.",
        llm=get_llm(),
        tools=ALL_TOOLS,
        system_prompt=MYCAREER_SYSTEM_PROMPT + MYCAREER_WELCOME_ADDENDUM,
        middleware=[
            create_summarization_middleware(),
            first_touch_profile_middleware,
            mycareer_personalization,
            profile_warning_middleware,
            tool_monitor_middleware,
        ],
        context_schema=MyCareerContext,
        checkpointer=checkpointer,
        context_factory=lambda thread_id: MyCareerContext(thread_id=thread_id),
    )
    return BaseAgent(config)


class MyCareerProtocol(AgentProtocol):
    """A2A protocol implementation for MyCareer agent."""

    def __init__(self, agent: BaseAgent):
        card = AgentCard(
            name="mycareer",
            description="Internal career management assistant",
            skills=[
                AgentSkill(name="profile_management", description="Analyze and improve user profiles", tags=["profile"]),
                AgentSkill(name="job_matching", description="Find matching internal job postings", tags=["jobs", "matching"]),
                AgentSkill(name="job_qa", description="Answer questions about job postings", tags=["jobs", "qa"]),
                AgentSkill(name="messaging", description="Draft and send messages to hiring managers", tags=["messaging"]),
                AgentSkill(name="applications", description="Submit job applications", tags=["jobs", "apply"]),
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
            context = MyCareerContext(**metadata)
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
