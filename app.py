"""
Chainlit entry point
"""

import json
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

from core.state import AppContext
from core.profile import load_profile
from agents.catalog import build_agent_catalog
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

def _build_app_context() -> AppContext:
    """Build an ``AppContext`` from the current Chainlit user session."""
    profile = load_profile()
    core = profile.get("core", {}) if profile else {}
    name_info = core.get("name", {})
    first_name = name_info.get("businessFirstName", "")
    display_name = f"{name_info.get('businessFirstName', '')} {name_info.get('businessLastName', '')}".strip()
    return AppContext(
        thread_id=cl.user_session.get("thread_id", ""),
        first_name=first_name,
        display_name=display_name,
    )


# ============================================================================
# AGENT INITIALISATION
# ============================================================================

checkpointer = InMemorySaver()
registry = build_agent_catalog(checkpointer=checkpointer)
orchestrator = create_orchestrator_agent(registry, checkpointer=checkpointer)


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
    """Initialize session — store the thread_id for context building."""
    cl.user_session.set("thread_id", cl.context.session.id)


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """Resume a previous chat session."""
    cl.user_session.set("thread_id", cl.context.session.id)

    profile = load_profile()
    core = profile.get("core", {}) if profile else {}
    name_info = core.get("name", {})
    first_name = name_info.get("businessFirstName", "")

    greeting = f"Welcome back, {first_name}!" if first_name else "Welcome back!"
    await cl.Message(content=f"{greeting} How can I help you today?").send()


# ============================================================================
# MESSAGE HANDLER
# ============================================================================

@cl.on_message
async def on_message(message: cl.Message):
    """Route every message through the orchestrator agent."""
    app_ctx = _build_app_context()

    response_text = ""
    all_elements: list = []

    async with cl.Step(name="Processing your request", type="tool") as step:
        try:
            result = await orchestrator.invoke(
                message.content,
                context=app_ctx,
            )

            messages = result.get("messages", [])

            # Slice to only the current turn (from the last HumanMessage onward)
            turn_start = 0
            for i, msg in enumerate(messages):
                if hasattr(msg, "type") and msg.type == "human":
                    turn_start = i
            current_turn_messages = messages[turn_start:]

            tool_calls = extract_tool_calls_from_messages(current_turn_messages)

            for tool_name, tool_result in tool_calls:
                elements = await render_tool_elements(tool_name, tool_result)
                all_elements.extend(elements)

            last_msg = current_turn_messages[-1] if current_turn_messages else None
            if last_msg:
                response_text = getattr(last_msg, "content", str(last_msg))

            step.output = _build_debug_output(current_turn_messages)

        except Exception as e:
            logger.exception("Error processing message")
            response_text = (
                "I'm sorry, something went wrong. Please try again. "
                f"({type(e).__name__})"
            )
            all_elements = []

    msg = cl.Message(content=response_text)
    if all_elements:
        msg.elements = all_elements
    await msg.send()


def _build_debug_output(messages: list) -> str:
    # Build a map from tool_call_id -> args so we can look up the input message
    tool_call_args: dict[str, dict] = {}
    for msg in messages:
        if not hasattr(msg, "type") or msg.type != "ai":
            continue
        for tc in getattr(msg, "tool_calls", []):
            tc_id = tc.get("id", "")
            if tc_id:
                tool_call_args[tc_id] = tc.get("args", {})

    parts = []
    for msg in messages:
        if not (hasattr(msg, "type") and msg.type == "tool"):
            continue

        tool_name = getattr(msg, "name", "")
        tool_call_id = getattr(msg, "tool_call_id", "")
        args = tool_call_args.get(tool_call_id, {})
        input_message = args.get("message", "")

        try:
            content = msg.content
            result = json.loads(content) if isinstance(content, str) else content
        except (json.JSONDecodeError, TypeError):
            result = {}

        if not isinstance(result, dict):
            result = {}

        header = f"▶ {tool_name}"
        if input_message:
            header += f'  ·  "{input_message}"'
        lines = [header]

        for inner in result.get("tool_calls", []):
            inner_name = inner.get("name", "")
            if inner_name:
                lines.append(f"  → {inner_name}")

        response = result.get("response", "")
        if response:
            lines.append(f"◀ {response}")

        parts.append("\n".join(lines))

    return "\n\n".join(parts) if parts else "No worker agents called."
