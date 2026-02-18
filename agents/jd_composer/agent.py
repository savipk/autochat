"""
JD Composer agent factory.
"""

from typing import Any

from pydantic import BaseModel

from core.llm import get_llm
from core.agent.base import BaseAgent
from core.agent.config import AgentConfig
from core.agent.protocol import AgentProtocol, AgentCard, AgentSkill, Task, TaskResult, TaskState, TaskMessage
from core.middleware.summarization import create_summarization_middleware
from core.middleware.tool_monitor import tool_monitor_middleware
from core.skills.base import Skill, SkillRegistry
from core.skills.loader import create_skill_loader_tool
from agents.jd_composer.middleware import jd_composer_personalization
from agents.jd_composer.prompts import JD_COMPOSER_SYSTEM_PROMPT
from agents.jd_composer.tools import ALL_TOOLS


class JDComposerContext(BaseModel):
    """Runtime context for JD Composer agent."""
    user_name: str = ""
    department: str = ""
    current_draft_id: str = ""


def create_jd_agent(checkpointer=None) -> BaseAgent:
    """Create and return a configured JD Composer agent."""
    skill_registry = SkillRegistry()
    skill_registry.register(Skill(
        name="jd_standards",
        description="Corporate job description standards covering tone, structure, and compliance guidelines.",
        path="agents/jd_composer/skills/jd_standards.md",
        tags=["standards", "compliance", "guidelines"],
    ))

    tools = ALL_TOOLS + [create_skill_loader_tool(skill_registry)]

    config = AgentConfig(
        name="jd_composer",
        description="Job Description Composer that helps hiring managers create standards-compliant JDs through an iterative, collaborative workflow.",
        llm=get_llm(),
        tools=tools,
        system_prompt=JD_COMPOSER_SYSTEM_PROMPT,
        middleware=[
            create_summarization_middleware(),
            jd_composer_personalization,
            tool_monitor_middleware,
        ],
        context_schema=JDComposerContext,
        checkpointer=checkpointer,
    )
    return BaseAgent(config)


class JDComposerProtocol(AgentProtocol):
    """A2A protocol implementation for JD Composer agent."""

    def __init__(self, agent: BaseAgent):
        card = AgentCard(
            name="jd_composer",
            description="Job Description Composer for hiring managers",
            skills=[
                AgentSkill(name="jd_search", description="Find similar past job descriptions", tags=["search", "rag"]),
                AgentSkill(name="jd_compose", description="Compose initial JD draft", tags=["compose", "draft"]),
                AgentSkill(name="section_editing", description="Edit individual JD sections", tags=["edit"]),
                AgentSkill(name="jd_finalize", description="Finalize JD for posting", tags=["finalize"]),
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
            context = JDComposerContext(**task.metadata) if task.metadata else None
            result = await self._agent.invoke(
                user_message,
                context=context,
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
