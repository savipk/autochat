"""
Chainlit entry point
"""

import json
import logging
import os
import sys

import chainlit as cl
from core.data_layer import SQLiteCompatibleDataLayer
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
    render_interrupt_elements,
    extract_tool_calls_from_messages,
    extract_interrupts_from_messages,
)
from core.profile_routes import router as profile_router, set_profile_updated, push_panel_event, register_user_metadata
from core.profile_manager import ProfileManager
from core.jd_routes import router as jd_router
from core.jd_manager import JDDraftManager


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
        register_user_metadata(username, user["profile_path"])
        return cl.User(
            identifier=username,
            metadata={"role": "user", "profile_path": user["profile_path"]},
        )
    return None


@cl.data_layer
def get_data_layer():
    """Persist chat threads so Chainlit can show sidebar history."""
    return SQLiteCompatibleDataLayer(conninfo="sqlite+aiosqlite:///./data/data.db")


# ============================================================================
# HELPERS
# ============================================================================

async def _sync_user_metadata_to_db(identifier: str, metadata: dict):
    """Update the user's metadata column in the DB so /user returns fresh data."""
    dl = get_data_layer()
    await dl.execute_sql(
        query="UPDATE users SET metadata = :metadata WHERE identifier = :identifier",
        parameters={"metadata": json.dumps(metadata), "identifier": identifier},
    )
    logger.info("Synced metadata to DB for user '%s'", identifier)


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

# Mount profile editor API routes on Chainlit's FastAPI app.
# We must insert our routes BEFORE Chainlit's catch-all "/{full_path:path}"
# route, otherwise the catch-all serves index.html for our SSE endpoint.
from chainlit.server import app as chainlit_app

chainlit_app.include_router(profile_router)
chainlit_app.include_router(jd_router)

# Move our API routes before Chainlit's catch-all by re-ordering the route list
_ours = [r for r in chainlit_app.routes if getattr(r, "path", "").startswith(("/api/profile", "/api/jd"))]
_rest = [r for r in chainlit_app.routes if r not in _ours]
chainlit_app.routes[:] = _ours + _rest


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

    # Sync persisted user metadata with auth config so the /user endpoint
    # returns up-to-date fields (e.g. profile_path).  The DB row created on
    # first login may have stale metadata if the auth_callback was updated
    # after the user was originally persisted.
    user = cl.user_session.get("user")
    if user:
        users_config = _get_users()
        config = users_config.get(user.identifier)
        if config:
            expected_metadata = {"role": "user", "profile_path": config["profile_path"]}
            if user.metadata != expected_metadata:
                user.metadata = expected_metadata
                try:
                    await _sync_user_metadata_to_db(user.identifier, expected_metadata)
                except Exception:
                    logger.debug("Failed to sync user metadata to DB", exc_info=True)

    # Emit user metadata so the side panel JS can read username + profile_path
    if user and hasattr(user, "metadata") and user.metadata:
        meta = {
            "username": user.identifier,
            "profile_path": user.metadata.get("profile_path", ""),
        }
        cl.user_session.set("profile_meta", meta)


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
# ACTION CALLBACKS — Human-in-the-loop for profile updates
# ============================================================================

@cl.action_callback("approve_profile_update")
async def approve_profile_update(action: cl.Action):
    """Accept a chat-agent-initiated profile change by resuming the interrupted graph."""
    payload = json.loads(action.payload) if isinstance(action.payload, str) else action.payload
    section = payload.get("section", "")
    username = payload.get("username", "")

    if not username:
        await cl.Message(content="Could not apply update — missing user context.").send()
        return

    # Resume the interrupted mycareer agent graph with an approve decision
    pending = cl.user_session.get("pending_interrupt")
    if not pending:
        await cl.Message(content="No pending update to approve.").send()
        return

    agent_name = pending.get("agent_name", "mycareer")
    parent_thread_id = pending.get("thread_id", "")
    namespaced_id = f"{parent_thread_id}:{agent_name}"

    try:
        agent = registry.get(agent_name)
        await agent.resume(
            {"decisions": [{"type": "approve"}]},
            thread_id=namespaced_id,
        )
    except Exception as e:
        logger.exception("Failed to resume agent for approval")
        await cl.Message(content=f"Error applying update: {type(e).__name__}").send()
        return

    set_profile_updated(username)

    # Clear middleware cache
    try:
        from agents.mycareer.middleware import clear_profile_cache
        clear_profile_cache()
    except ImportError:
        pass

    cl.user_session.set("pending_interrupt", None)
    if section == "rollback":
        await cl.Message(content="Profile restored from backup.").send()
    else:
        await cl.Message(content=f"Profile updated: **{section}** section saved.").send()


@cl.action_callback("reject_profile_update")
async def reject_profile_update(action: cl.Action):
    """Decline a chat-agent-initiated profile change."""
    pending = cl.user_session.get("pending_interrupt")
    section = ""
    if pending:
        agent_name = pending.get("agent_name", "mycareer")
        parent_thread_id = pending.get("thread_id", "")
        namespaced_id = f"{parent_thread_id}:{agent_name}"
        section = pending.get("section", "")
        try:
            agent = registry.get(agent_name)
            await agent.resume(
                {"decisions": [{"type": "reject", "message": "User declined the update."}]},
                thread_id=namespaced_id,
            )
        except Exception:
            logger.debug("Failed to resume agent for rejection", exc_info=True)
        cl.user_session.set("pending_interrupt", None)
    if section == "rollback":
        await cl.Message(content="Rollback declined. No changes were made.").send()
    else:
        await cl.Message(content="Profile update declined. No changes were made.").send()


# ============================================================================
# MESSAGE HANDLER
# ============================================================================

_APPROVE_PHRASES = {"approve", "accept", "yes", "sure", "go ahead", "ok", "okay", "confirm", "yep", "yeah", "y"}
_REJECT_PHRASES = {"reject", "decline", "no", "cancel", "nope", "nah", "n"}


async def _handle_pending_interrupt(user_text: str) -> bool | None:
    """If there is a pending HITL interrupt, decide whether to approve, reject,
    or auto-reject (for unrelated messages).

    Returns ``True`` if the interrupt was handled (caller should stop),
    ``None`` if there was no pending interrupt (caller should continue normally).
    """
    pending = cl.user_session.get("pending_interrupt")
    if not pending:
        return None

    agent_name = pending.get("agent_name", "mycareer")
    parent_thread_id = pending.get("thread_id", "")
    namespaced_id = f"{parent_thread_id}:{agent_name}"
    section = pending.get("section", "profile")

    normalised = user_text.strip().lower().rstrip("!.,")

    if normalised in _APPROVE_PHRASES:
        decision = {"decisions": [{"type": "approve"}]}
        try:
            agent = registry.get(agent_name)
            await agent.resume(decision, thread_id=namespaced_id)
        except Exception as e:
            logger.exception("Failed to resume agent for chat-based approval")
            await cl.Message(content=f"Error applying update: {type(e).__name__}").send()
            cl.user_session.set("pending_interrupt", None)
            return True

        user = cl.user_session.get("user")
        username = user.identifier if user else ""
        if username:
            set_profile_updated(username)
        try:
            from agents.mycareer.middleware import clear_profile_cache
            clear_profile_cache()
        except ImportError:
            pass

        cl.user_session.set("pending_interrupt", None)
        if section == "rollback":
            await cl.Message(content="Profile restored from backup.").send()
        else:
            await cl.Message(content=f"Profile updated: **{section}** section saved.").send()
        return True

    if normalised in _REJECT_PHRASES:
        decision = {"decisions": [{"type": "reject", "message": "User declined via chat."}]}
        try:
            agent = registry.get(agent_name)
            await agent.resume(decision, thread_id=namespaced_id)
        except Exception:
            logger.debug("Failed to resume agent for chat-based rejection", exc_info=True)
        cl.user_session.set("pending_interrupt", None)
        if section == "rollback":
            await cl.Message(content="Rollback declined. No changes were made.").send()
        else:
            await cl.Message(content="Profile update declined. No changes were made.").send()
        return True

    # Unrelated message — auto-reject the pending interrupt to clean graph state,
    # then let the caller continue with normal message processing.
    try:
        agent = registry.get(agent_name)
        await agent.resume(
            {"decisions": [{"type": "reject", "message": "Superseded by new user message."}]},
            thread_id=namespaced_id,
        )
    except Exception:
        logger.debug("Failed to auto-clear pending interrupt", exc_info=True)
    cl.user_session.set("pending_interrupt", None)
    return None


@cl.on_message
async def on_message(message: cl.Message):
    """Route every message through the orchestrator agent."""
    # Handle pending HITL interrupts before routing to the orchestrator.
    handled = await _handle_pending_interrupt(message.content)
    if handled:
        return

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
            pending_interrupts = extract_interrupts_from_messages(current_turn_messages)

            # If the agent opened the profile panel, push the SSE event now
            # (post-orchestrator) so the browser can load data reliably.
            user = cl.user_session.get("user")
            username = user.identifier if user else ""
            profile_path = ""
            if user and hasattr(user, "metadata") and user.metadata:
                profile_path = user.metadata.get("profile_path", "")

            if username:
                for tool_name, _tool_result in tool_calls:
                    if tool_name == "open_profile_panel":
                        push_panel_event(username, "open_panel")
                    elif tool_name == "view_job":
                        if isinstance(_tool_result, dict) and _tool_result.get("job_id"):
                            push_panel_event(username, "open_jd_panel", data={
                                "job_id": _tool_result["job_id"],
                                "job": _tool_result.get("job", {}),
                            })
                    elif tool_name == "jd_compose":
                        if isinstance(_tool_result, dict) and _tool_result.get("success"):
                            try:
                                jd_mgr = JDDraftManager(username)
                                jd_mgr.save_draft(_tool_result)
                                push_panel_event(username, "open_jd_editor")
                            except Exception:
                                logger.debug("Failed to save JD draft", exc_info=True)
                    elif tool_name == "section_editor":
                        if isinstance(_tool_result, dict) and _tool_result.get("success"):
                            try:
                                jd_mgr = JDDraftManager(username)
                                section = _tool_result.get("section", "")
                                content = _tool_result.get("updated_content", "")
                                if section and content:
                                    jd_mgr.update_section(section, content)
                                push_panel_event(username, "refresh_jd_editor")
                            except Exception:
                                logger.debug("Failed to update JD draft section", exc_info=True)

            # Handle human-in-the-loop interrupts (e.g. update_profile approval)
            if pending_interrupts:
                for intr_info in pending_interrupts:
                    intr_elements = await render_interrupt_elements(
                        [intr_info["interrupt"]],
                        agent_name=intr_info["agent_name"],
                        profile_path=profile_path,
                        username=username,
                    )
                    all_elements.extend(intr_elements)
                    # Extract section from interrupt for session metadata
                    intr_section = "profile"
                    intr_value = intr_info["interrupt"].get("value", {})
                    for ar in intr_value.get("action_requests", []):
                        if ar.get("name") == "update_profile":
                            intr_section = ar.get("args", {}).get("section", "profile")
                            break
                        elif ar.get("name") == "rollback_profile":
                            intr_section = "rollback"
                            break

                    # Store interrupt metadata in session for resume
                    cl.user_session.set("pending_interrupt", {
                        "agent_name": intr_info["agent_name"],
                        "thread_id": cl.user_session.get("thread_id", ""),
                        "section": intr_section,
                    })

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


def _build_debug_output(messages: list) -> str:
    # Build a map from tool_call_id -> tool_call so we can look up args
    tool_call_map: dict[str, dict] = {}
    for msg in messages:
        if not hasattr(msg, "type") or msg.type != "ai":
            continue
        for tc in getattr(msg, "tool_calls", []):
            tc_id = tc.get("id", "")
            if tc_id:
                tool_call_map[tc_id] = tc

    parts = []

    # 1. User → Orchestrator
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "human":
            user_text = msg.content if isinstance(msg.content, str) else str(msg.content)
            parts.append(f"━━━ User → Orchestrator ━━━\n\"{user_text}\"")
            break

    # 2. Each AIMessage with tool_calls = orchestrator delegating to a worker agent
    tool_messages: dict[str, object] = {}
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "tool":
            tc_id = getattr(msg, "tool_call_id", "")
            if tc_id:
                tool_messages[tc_id] = msg

    for msg in messages:
        if not (hasattr(msg, "type") and msg.type == "ai"):
            continue
        tool_calls = getattr(msg, "tool_calls", [])
        if not tool_calls:
            continue

        for tc in tool_calls:
            agent_name = tc.get("name", "worker")
            args = tc.get("args", {})
            delegated_message = args.get("message", "")
            tc_id = tc.get("id", "")

            # Orchestrator → Worker header
            section_lines = [f"━━━ Orchestrator → {agent_name} (worker agent) ━━━"]
            if delegated_message:
                section_lines.append(f'"{delegated_message}"')

            # Find the corresponding ToolMessage
            tool_msg = tool_messages.get(tc_id)
            result = {}
            if tool_msg is not None:
                try:
                    raw = tool_msg.content
                    result = json.loads(raw) if isinstance(raw, str) else raw
                except (json.JSONDecodeError, TypeError):
                    result = {}
                if not isinstance(result, dict):
                    result = {}

            # Inner tool calls made by the worker agent
            for inner in result.get("tool_calls", []):
                inner_name = inner.get("name", "")
                inner_content = inner.get("content", "")
                if inner_name:
                    section_lines.append(f"  ▶ {agent_name} → {inner_name}")
                    summary = _summarize_tool_content(inner_content)
                    section_lines.append(f"  ◀ {inner_name} → {agent_name}: {summary}")

            parts.append("\n".join(section_lines))

            # Worker → Orchestrator
            response = result.get("response", "")
            if response:
                resp_preview = response[:200] + ("…" if len(response) > 200 else "")
                parts.append(f"━━━ {agent_name} → Orchestrator ━━━\n\"{resp_preview}\"")

    # 3. Last AIMessage without tool_calls = final orchestrator reply to user
    final_ai = None
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "ai" and not getattr(msg, "tool_calls", []):
            final_ai = msg
    if final_ai is not None:
        final_text = final_ai.content if isinstance(final_ai.content, str) else str(final_ai.content)
        preview = final_text[:200] + ("…" if len(final_text) > 200 else "")
        parts.append(f"━━━ Orchestrator → User ━━━\n\"{preview}\"")

    return "\n\n".join(parts) if parts else "No worker agents called."


# def _build_debug_output(messages: list) -> str:
#     """Dump every message in the current turn with its full, untruncated data."""
#     parts = []

#     for idx, msg in enumerate(messages):
#         msg_type = getattr(msg, "type", type(msg).__name__)
#         header = f"━━━ Message {idx} | type={msg_type} ━━━"

#         body_lines = []

#         # Full content (no truncation)
#         content = getattr(msg, "content", None)
#         if content is not None:
#             if isinstance(content, str):
#                 try:
#                     parsed = json.loads(content)
#                     body_lines.append(f"content:\n{json.dumps(parsed, indent=2, default=str)}")
#                 except (json.JSONDecodeError, TypeError):
#                     body_lines.append(f"content:\n{content}")
#             else:
#                 body_lines.append(f"content:\n{json.dumps(content, indent=2, default=str)}")

#         # Tool calls on AI messages (full args, no summarisation)
#         tool_calls = getattr(msg, "tool_calls", None)
#         if tool_calls:
#             body_lines.append(f"tool_calls ({len(tool_calls)}):")
#             for tc in tool_calls:
#                 body_lines.append(json.dumps(tc, indent=2, default=str))

#         # tool_call_id on ToolMessages
#         tool_call_id = getattr(msg, "tool_call_id", None)
#         if tool_call_id:
#             body_lines.append(f"tool_call_id: {tool_call_id}")

#         # name (tool name on ToolMessages)
#         name = getattr(msg, "name", None)
#         if name:
#             body_lines.append(f"name: {name}")

#         # additional_kwargs (often contains raw function_call data)
#         additional = getattr(msg, "additional_kwargs", None)
#         if additional:
#             body_lines.append(f"additional_kwargs:\n{json.dumps(additional, indent=2, default=str)}")

#         # response_metadata (model info, token usage, etc.)
#         resp_meta = getattr(msg, "response_metadata", None)
#         if resp_meta:
#             body_lines.append(f"response_metadata:\n{json.dumps(resp_meta, indent=2, default=str)}")

#         parts.append(header + "\n" + "\n".join(body_lines) if body_lines else header)

#     return "\n\n".join(parts) if parts else "No messages in current turn."
