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

def _get_users() -> dict:
    return {
        "admin": {
            "password": os.getenv("CL_ADMIN_PASS", "admin"),
            "profile_path": "data/sample_profile.json",
        },
        "travis": {
            "password": os.getenv("CL_TRAVIS_PASS", "travis"),
            "profile_path": "data/sample_profile.json",
        },
        "john": {
            "password": os.getenv("CL_JOHN_PASS", "john"),
            "profile_path": "data/low_profile_eval.json",
        },
        "rob": {
            "password": os.getenv("CL_ROB_PASS", "rob"),
            "profile_path": "data/rob_profile.json",
        },
        "miro": {
            "password": os.getenv("CL_MIRO_PASS", "miro"),
            "profile_path": "data/miro_profile.json",
        },
    }


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """Multi-user auth with per-user profile mapping."""
    users = _get_users()
    user = users.get(username)
    if user and password == user["password"]:
        return cl.User(
            identifier=username,
            metadata={"role": "user", "profile_path": user["profile_path"]},
        )
    return None


@cl.data_layer
def get_data_layer():
    """Persist chat threads so Chainlit can show sidebar history."""
    return SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///./data/data.db")


# ============================================================================
# HELPERS
# ============================================================================

def _profile_path_for_session() -> str | None:
    user = cl.user_session.get("user")
    if user and hasattr(user, "metadata") and user.metadata:
        return user.metadata.get("profile_path")
    return None


def _build_app_context() -> AppContext:
    """Build an ``AppContext`` from the current Chainlit user session."""
    profile = load_profile(_profile_path_for_session())
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

    profile = load_profile(_profile_path_for_session())
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


def _summarize_tool_content(content) -> str:
    """Return a short human-readable summary of an inner tool result."""
    if isinstance(content, str):
        return content[:120] + ("…" if len(content) > 120 else "")
    if not isinstance(content, dict):
        return str(content)[:120]
    # Pull out meaningful fields when present
    meaningful = {}
    for key in ("success", "count", "completionScore", "topSkills", "error", "message"):
        if key in content:
            meaningful[key] = content[key]
    if meaningful:
        return ", ".join(f"{k}={v}" for k, v in meaningful.items())
    # Fall back to listing keys
    keys = list(content.keys())
    summary = f"{{{', '.join(keys[:6])}}}"
    if len(keys) > 6:
        summary += f" (+{len(keys) - 6} more)"
    return summary


# def _build_debug_output_old(messages: list) -> str:
#     # Build a map from tool_call_id -> tool_call so we can look up args
#     tool_call_map: dict[str, dict] = {}
#     for msg in messages:
#         if not hasattr(msg, "type") or msg.type != "ai":
#             continue
#         for tc in getattr(msg, "tool_calls", []):
#             tc_id = tc.get("id", "")
#             if tc_id:
#                 tool_call_map[tc_id] = tc
#
#     parts = []
#
#     # 1. User → Orchestrator
#     for msg in messages:
#         if hasattr(msg, "type") and msg.type == "human":
#             user_text = msg.content if isinstance(msg.content, str) else str(msg.content)
#             parts.append(f"━━━ User → Orchestrator ━━━\n\"{user_text}\"")
#             break
#
#     # 2. Each AIMessage with tool_calls = orchestrator delegating to a worker agent
#     tool_messages: dict[str, object] = {}
#     for msg in messages:
#         if hasattr(msg, "type") and msg.type == "tool":
#             tc_id = getattr(msg, "tool_call_id", "")
#             if tc_id:
#                 tool_messages[tc_id] = msg
#
#     for msg in messages:
#         if not (hasattr(msg, "type") and msg.type == "ai"):
#             continue
#         tool_calls = getattr(msg, "tool_calls", [])
#         if not tool_calls:
#             continue
#
#         for tc in tool_calls:
#             agent_name = tc.get("name", "worker")
#             args = tc.get("args", {})
#             delegated_message = args.get("message", "")
#             tc_id = tc.get("id", "")
#
#             # Orchestrator → Worker header
#             section_lines = [f"━━━ Orchestrator → {agent_name} (worker agent) ━━━"]
#             if delegated_message:
#                 section_lines.append(f'"{delegated_message}"')
#
#             # Find the corresponding ToolMessage
#             tool_msg = tool_messages.get(tc_id)
#             result = {}
#             if tool_msg is not None:
#                 try:
#                     raw = tool_msg.content
#                     result = json.loads(raw) if isinstance(raw, str) else raw
#                 except (json.JSONDecodeError, TypeError):
#                     result = {}
#                 if not isinstance(result, dict):
#                     result = {}
#
#             # Inner tool calls made by the worker agent
#             for inner in result.get("tool_calls", []):
#                 inner_name = inner.get("name", "")
#                 inner_content = inner.get("content", "")
#                 if inner_name:
#                     section_lines.append(f"  ▶ {agent_name} → {inner_name}")
#                     summary = _summarize_tool_content(inner_content)
#                     section_lines.append(f"  ◀ {inner_name} → {agent_name}: {summary}")
#
#             parts.append("\n".join(section_lines))
#
#             # Worker → Orchestrator
#             response = result.get("response", "")
#             if response:
#                 resp_preview = response[:200] + ("…" if len(response) > 200 else "")
#                 parts.append(f"━━━ {agent_name} → Orchestrator ━━━\n\"{resp_preview}\"")
#
#     # 3. Last AIMessage without tool_calls = final orchestrator reply to user
#     final_ai = None
#     for msg in messages:
#         if hasattr(msg, "type") and msg.type == "ai" and not getattr(msg, "tool_calls", []):
#             final_ai = msg
#     if final_ai is not None:
#         final_text = final_ai.content if isinstance(final_ai.content, str) else str(final_ai.content)
#         preview = final_text[:200] + ("…" if len(final_text) > 200 else "")
#         parts.append(f"━━━ Orchestrator → User ━━━\n\"{preview}\"")
#
#     return "\n\n".join(parts) if parts else "No worker agents called."


def _build_debug_output(messages: list) -> str:
    """Dump every message in the current turn with its full, untruncated data."""
    parts = []

    for idx, msg in enumerate(messages):
        msg_type = getattr(msg, "type", type(msg).__name__)
        header = f"━━━ Message {idx} | type={msg_type} ━━━"

        body_lines = []

        # Full content (no truncation)
        content = getattr(msg, "content", None)
        if content is not None:
            if isinstance(content, str):
                try:
                    parsed = json.loads(content)
                    body_lines.append(f"content:\n{json.dumps(parsed, indent=2, default=str)}")
                except (json.JSONDecodeError, TypeError):
                    body_lines.append(f"content:\n{content}")
            else:
                body_lines.append(f"content:\n{json.dumps(content, indent=2, default=str)}")

        # Tool calls on AI messages (full args, no summarisation)
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            body_lines.append(f"tool_calls ({len(tool_calls)}):")
            for tc in tool_calls:
                body_lines.append(json.dumps(tc, indent=2, default=str))

        # tool_call_id on ToolMessages
        tool_call_id = getattr(msg, "tool_call_id", None)
        if tool_call_id:
            body_lines.append(f"tool_call_id: {tool_call_id}")

        # name (tool name on ToolMessages)
        name = getattr(msg, "name", None)
        if name:
            body_lines.append(f"name: {name}")

        # additional_kwargs (often contains raw function_call data)
        additional = getattr(msg, "additional_kwargs", None)
        if additional:
            body_lines.append(f"additional_kwargs:\n{json.dumps(additional, indent=2, default=str)}")

        # response_metadata (model info, token usage, etc.)
        resp_meta = getattr(msg, "response_metadata", None)
        if resp_meta:
            body_lines.append(f"response_metadata:\n{json.dumps(resp_meta, indent=2, default=str)}")

        parts.append(header + "\n" + "\n".join(body_lines) if body_lines else header)

    return "\n\n".join(parts) if parts else "No messages in current turn."
