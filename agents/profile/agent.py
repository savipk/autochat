"""
Profile agent factory.
"""

from core.llm import get_llm
from core.state import BaseContext
from core.agent.base import BaseAgent
from core.agent.config import AgentConfig
from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill, Task, TaskResult, TaskState, TaskMessage
from langchain.agents.middleware import HumanInTheLoopMiddleware
from core.middleware.summarization import create_summarization_middleware
from core.middleware.tool_monitor import tool_monitor_middleware
from agents.shared.middleware import first_touch_profile_middleware, employee_personalization
from agents.profile.prompts import PROFILE_SYSTEM_PROMPT, PROFILE_WELCOME_ADDENDUM
from agents.profile.tools import PROFILE_TOOLS


class ProfileContext(BaseContext):
    """Runtime context for Profile agent."""
    completion_score: int = 100


def create_profile_agent(checkpointer=None) -> BaseAgent:
    """Create and return a configured Profile agent."""
    config = AgentConfig(
        name="profile",
        description="Helps employees analyse and improve their profile, infer skills, and manage work history and preferences.",
        llm=get_llm(),
        tools=PROFILE_TOOLS,
        system_prompt=PROFILE_SYSTEM_PROMPT + PROFILE_WELCOME_ADDENDUM,
        middleware=[
            create_summarization_middleware(),
            first_touch_profile_middleware,
            employee_personalization,
            tool_monitor_middleware,
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "update_profile": {"allowed_decisions": ["approve", "reject"]},
                    "rollback_profile": {"allowed_decisions": ["approve", "reject"]},
                },
            ),
        ],
        context_schema=ProfileContext,
        checkpointer=checkpointer,
        context_factory=lambda thread_id: ProfileContext(thread_id=thread_id),
    )
    return BaseAgent(config)


class ProfileProtocol(AgentProtocol):
    """A2A protocol implementation for Profile agent."""

    def __init__(self, agent: BaseAgent):
        card = AgentCard(
            name="profile",
            description="Profile management assistant for employees",
            skills=[
                AgentSkill(name="analyze_profile", description="Analyze profile completion and provide recommendations", tags=["profile", "analysis"]),
                AgentSkill(name="suggest_skills", description="Infer and suggest skills from experience", tags=["profile", "skills"]),
                AgentSkill(name="update_profile", description="Add, edit, or remove profile entries", tags=["profile", "update"]),
                AgentSkill(name="rollback_profile", description="Undo recent profile changes", tags=["profile", "rollback"]),
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
            context = ProfileContext(**metadata)
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
