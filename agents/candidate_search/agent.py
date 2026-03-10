"""
Candidate Search agent factory.
"""

from core.llm import get_llm
from core.state import BaseContext
from core.agent.base import BaseAgent
from core.agent.config import AgentConfig
from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill, Task, TaskResult, TaskState, TaskMessage
from core.middleware.summarization import create_summarization_middleware
from core.middleware.tool_monitor import tool_monitor_middleware
from agents.candidate_search.middleware import candidate_search_personalization
from agents.candidate_search.prompts import CANDIDATE_SEARCH_SYSTEM_PROMPT, CANDIDATE_SEARCH_WELCOME_ADDENDUM
from agents.candidate_search.tools import CANDIDATE_SEARCH_TOOLS


class CandidateSearchContext(BaseContext):
    """Runtime context for Candidate Search agent."""


def create_candidate_search_agent(checkpointer=None) -> BaseAgent:
    """Create and return a configured Candidate Search agent."""
    config = AgentConfig(
        name="candidate_search",
        description="Helps hiring managers find internal employees by skills, level, location, and department, and view detailed candidate profiles.",
        llm=get_llm(),
        tools=CANDIDATE_SEARCH_TOOLS,
        system_prompt=CANDIDATE_SEARCH_SYSTEM_PROMPT + CANDIDATE_SEARCH_WELCOME_ADDENDUM,
        middleware=[
            create_summarization_middleware(),
            candidate_search_personalization,
            tool_monitor_middleware,
        ],
        context_schema=CandidateSearchContext,
        checkpointer=checkpointer,
        context_factory=lambda thread_id: CandidateSearchContext(thread_id=thread_id),
    )
    return BaseAgent(config)


class CandidateSearchProtocol(AgentProtocol):
    """A2A protocol implementation for Candidate Search agent."""

    def __init__(self, agent: BaseAgent):
        card = AgentCard(
            name="candidate_search",
            description="Candidate search assistant for hiring managers",
            skills=[
                AgentSkill(name="search_candidates", description="Search internal employees by skills, level, location, department", tags=["search", "candidates"]),
                AgentSkill(name="view_candidate", description="View detailed candidate profile", tags=["candidate", "profile"]),
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
            context = CandidateSearchContext(**metadata)
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
