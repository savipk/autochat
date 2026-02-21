"""
Chainlit entry point
"""

import logging
import os
import sys

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.types import ThreadDict
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

sys.path.insert(0, os.path.dirname(__file__))

from agents.mycareer.agent import MyCareerContext, create_mycareer_agent
from agents.jd_generator.agent import create_jd_agent
from agents.orchestrator.agent import create_orchestrator_agent
from core.adapters.chainlit_adapter import (
    render_tool_elements,
    extract_tool_calls_from_messages,
)


# ============================================================================
# DATA LAYER
# ============================================================================

@cl.data_layer
def get_data_layer():
    """Persist chat threads so Chainlit can show sidebar history."""
    return SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///./data/data.db")


# ============================================================================
# HELPERS
# ============================================================================

def _build_mycareer_context() -> MyCareerContext:
    """Build a ``MyCareerContext`` from the current Chainlit user session."""
    return MyCareerContext(
        completion_score=cl.user_session.get("completion_score", 100),
    )


# ============================================================================
# AGENT INITIALISATION
# ============================================================================

checkpointer = InMemorySaver()
mycareer_agent = create_mycareer_agent(checkpointer=checkpointer)
jd_agent = create_jd_agent(checkpointer=checkpointer)
orchestrator = create_orchestrator_agent(mycareer_agent, jd_agent, checkpointer=checkpointer)


# ============================================================================
# STARTERS
# ============================================================================

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Improve your profile",
            message="I'd like to improve my profile",
            icon="/public/idea.svg",
        ),
        cl.Starter(
            label="Find roles",
            message="Help me find matching roles",
            icon="/public/idea.svg",
        ),
        cl.Starter(
            label="Create a JD",
            message="I need to create a job description",
            icon="/public/idea.svg",
        ),
    ]


# ============================================================================
# CHAT LIFECYCLE
# ============================================================================

@cl.on_chat_start
async def on_chat_start():
    """Initialize session -- compute completion score and set up tracking state."""
    cl.user_session.set("thread_id", cl.context.session.id)

    from agents.mycareer.tools.profile_analyzer import run_profile_analyzer

    analysis = run_profile_analyzer()
    cl.user_session.set("completion_score", analysis.get("completionScore", 100))


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """Resume a previous chat session -- recompute completion score."""
    cl.user_session.set("thread_id", cl.context.session.id)

    from agents.mycareer.tools.profile_analyzer import run_profile_analyzer

    analysis = run_profile_analyzer()
    cl.user_session.set("completion_score", analysis.get("completionScore", 100))

    await cl.Message(content="Welcome back! How can I help you today?").send()


# ============================================================================
# MESSAGE HANDLER
# ============================================================================

@cl.on_message
async def on_message(message: cl.Message):
    """Route every message through the orchestrator agent."""
    thread_id = cl.user_session.get("thread_id", "")
    mycareer_ctx = _build_mycareer_context()

    msg = cl.Message(content="")
    await msg.send()

    async with cl.Step(name="Processing your request", type="tool") as step:
        try:
            result = await orchestrator.invoke(
                message.content,
                context=mycareer_ctx,
                thread_id=thread_id,
            )

            messages = result.get("messages", [])

            all_elements: list = []
            tool_calls = extract_tool_calls_from_messages(messages)

            for tool_name, tool_result in tool_calls:
                elements = await render_tool_elements(tool_name, tool_result)
                all_elements.extend(elements)

            last_msg = messages[-1] if messages else None
            response_text = ""
            if last_msg:
                response_text = getattr(last_msg, "content", str(last_msg))

            step.output = _build_debug_output(tool_calls, response_text)

        except Exception as e:
            logger.exception("Error processing message")
            response_text = (
                "I'm sorry, something went wrong. Please try again. "
                f"({type(e).__name__})"
            )
            all_elements = []

    msg.content = response_text
    if all_elements:
        msg.elements = all_elements
    await msg.update()


def _build_debug_output(tool_calls: list[tuple[str, dict]], response_text: str) -> str:
    parts = []
    if tool_calls:
        parts.append("Tools executed: " + ", ".join(t[0] for t in tool_calls))
    if response_text:
        snippet = response_text[:200]
        parts.append(f"Response preview: {snippet}")
    return "\n".join(parts) if parts else "No tools executed."
