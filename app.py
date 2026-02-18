"""
AutoChat -- Chainlit entry point.

Single chat window with concierge orchestration.
No auto-welcome; starters shown on start screen.
"""

import json
import logging
import os
import sys

import chainlit as cl
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autochat")

sys.path.insert(0, os.path.dirname(__file__))

from agents.mycareer.agent import create_mycareer_agent
from agents.jd_composer.agent import create_jd_agent
from agents.concierge.agent import create_concierge_agent
from core.adapters.chainlit_adapter import (
    render_tool_elements,
    extract_tool_calls_from_messages,
)


def load_profile(path: str) -> dict:
    """Load a user profile from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


checkpointer = InMemorySaver()
mycareer_agent = create_mycareer_agent(checkpointer=checkpointer)
jd_agent = create_jd_agent(checkpointer=checkpointer)
concierge = create_concierge_agent(mycareer_agent, jd_agent, checkpointer=checkpointer)


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


@cl.on_chat_start
async def on_chat_start():
    """Initialize session -- load profile, no welcome message."""
    profile_path = os.getenv("PROFILE_PATH", "data/miro_profile.json")
    profile = load_profile(profile_path)
    cl.user_session.set("profile", profile)
    cl.user_session.set("thread_id", cl.context.session.id)

    from agents.mycareer.tools.profile_analyzer import run_profile_analyzer
    analysis = run_profile_analyzer(profile)
    cl.user_session.set("completion_score", analysis.get("completionScore", 100))


@cl.on_message
async def on_message(message: cl.Message):
    """Route every message through the concierge agent."""
    profile = cl.user_session.get("profile", {})
    thread_id = cl.user_session.get("thread_id", "")
    completion_score = cl.user_session.get("completion_score", 100)

    msg = cl.Message(content="")
    await msg.send()

    try:
        result = await concierge.invoke(
            message.content,
            thread_id=thread_id,
        )

        messages = result.get("messages", [])

        all_elements = []
        tool_calls = extract_tool_calls_from_messages(messages)
        for tool_name, tool_result in tool_calls:
            elements = await render_tool_elements(tool_name, tool_result)
            all_elements.extend(elements)

        last_msg = messages[-1] if messages else None
        response_text = ""
        if last_msg:
            response_text = getattr(last_msg, "content", str(last_msg))

        msg.content = response_text
        if all_elements:
            msg.elements = all_elements
        await msg.update()

    except Exception as e:
        logger.exception("Error processing message")
        msg.content = f"I'm sorry, something went wrong. Please try again. ({type(e).__name__})"
        await msg.update()
