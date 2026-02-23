"""
Chainlit adapter -- bridges the Chainlit UI with the orchestrator agent.

Handles:
- Rendering Chainlit elements (JobCard, DraftMessage, ProfileScore) from tool results

Tool response rendering follows a prompt-driven pattern: the LLM system prompt
instructs the model not to repeat data that is shown via custom elements (e.g.
job cards, skill lists, draft message bodies).  The mapping is:

  get_matches     -> LLM intro text + JobCard elements       (LLM before elements)
  infer_skills    -> LLM intro text + skills Text element     (LLM before elements)
  profile_analyzer-> LLM text + ProfileScore element          (LLM before elements)
  draft_message   -> LLM text + DraftMessage element          (LLM around elements)
  send_message    -> confirmation Text element (LLM only)
  apply_for_role  -> confirmation Text element (LLM only)
  ask_jd_qa       -> LLM text + Q&A citation Text element
  update_profile  -> LLM text + profile update confirmation Text element
  jd_search       -> LLM text + similar JDs Text element
  jd_finalize     -> LLM text + finalization summary Text element
"""

from __future__ import annotations

import json
import logging
from typing import Any

import chainlit as cl

logger = logging.getLogger("chatbot.adapter")


async def render_tool_elements(tool_name: str, tool_result: dict[str, Any]) -> list:
    """Create Chainlit elements from tool results."""
    elements: list = []

    if tool_name == "get_matches":
        matches = tool_result.get("matches", [])
        for job in matches:
            elements.append(cl.CustomElement(name="JobCard", props=job))

    elif tool_name == "profile_analyzer":
        elements.append(cl.CustomElement(name="ProfileScore", props={
            "completionScore": tool_result.get("completionScore", 0),
            "sectionScores": tool_result.get("sectionScores", {}),
            "missingSections": tool_result.get("missingSections", []),
        }))

    elif tool_name == "draft_message":
        elements.append(cl.CustomElement(name="DraftMessage", props={
            "recipient_name": tool_result.get("recipient_name", ""),
            "sender_name": tool_result.get("sender_name", ""),
            "message_body": tool_result.get("message_body", ""),
            "job_title": tool_result.get("job_title", ""),
            "message_type": tool_result.get("message_type", "teams"),
        }))

    elif tool_name == "infer_skills":
        top = tool_result.get("topSkills", [])
        additional = tool_result.get("additionalSkills", [])
        if top or additional:
            content = ""
            if top:
                content += "**Top Skills:** " + ", ".join(top) + "\n\n"
            if additional:
                content += "**Additional Skills:** " + ", ".join(additional)
            elements.append(cl.Text(
                name="suggested_skills",
                content=content,
                display="inline",
            ))

    elif tool_name == "send_message":
        if tool_result.get("success"):
            recipient = tool_result.get("recipient_name", "recipient")
            msg_type = tool_result.get("message_type", "Teams")
            sent_at = tool_result.get("sent_at", "")
            text = f"Message sent to **{recipient}** via {msg_type}"
            if sent_at:
                text += f" at {sent_at}"
            text += "."
            elements.append(cl.Text(
                name="send_confirmation",
                content=text,
                display="inline",
            ))

    elif tool_name == "apply_for_role":
        if tool_result.get("success"):
            job_title = tool_result.get("job_title", "the role")
            app_id = tool_result.get("application_id", "")
            text = f"Application submitted for **{job_title}**."
            if app_id:
                text += f"  \nApplication ID: `{app_id}`"
            elements.append(cl.Text(
                name="apply_confirmation",
                content=text,
                display="inline",
            ))

    elif tool_name == "update_profile":
        if tool_result.get("success"):
            section = tool_result.get("section", "profile")
            updated = tool_result.get("updated_fields", {})
            prev_score = tool_result.get("previous_completion_score", 0)
            new_score = tool_result.get("estimated_new_score", 0)
            parts = [f"**Section updated:** {section}"]
            for field_name, field_value in updated.items():
                if isinstance(field_value, list):
                    parts.append(f"- **{field_name}:** {', '.join(str(v) for v in field_value)}")
                else:
                    parts.append(f"- **{field_name}:** {field_value}")
            if prev_score or new_score:
                parts.append(f"\nCompletion score: {prev_score}% -> {new_score}% (estimated)")
            elements.append(cl.Text(
                name="profile_update",
                content="\n".join(parts),
                display="inline",
            ))

    elif tool_name == "ask_jd_qa":
        if tool_result.get("success"):
            citations = tool_result.get("citations", [])
            job_title = tool_result.get("job_title", "")
            hiring_manager = tool_result.get("hiring_manager", "")
            parts = []
            if job_title:
                parts.append(f"**Role:** {job_title}")
            if hiring_manager:
                parts.append(f"**Hiring Manager:** {hiring_manager}")
            if citations:
                parts.append("**Sources:** " + ", ".join(citations))
            if tool_result.get("suggest_contact_hiring_manager"):
                parts.append("\n_Tip: Consider contacting the hiring manager for more details._")
            if parts:
                elements.append(cl.Text(
                    name="jd_qa_info",
                    content="\n".join(parts),
                    display="inline",
                ))

    elif tool_name == "jd_search":
        similar_jds = tool_result.get("similar_jds", [])
        if similar_jds:
            parts = []
            for jd in similar_jds:
                score = jd.get("similarity_score", 0)
                parts.append(
                    f"- **{jd.get('title', 'Untitled')}** ({jd.get('level', '')}, "
                    f"{jd.get('department', '')}) -- similarity: {score:.0%}"
                )
            elements.append(cl.Text(
                name="similar_jds",
                content="**Similar Past JDs:**\n" + "\n".join(parts),
                display="inline",
            ))

    elif tool_name == "jd_finalize":
        if tool_result.get("success"):
            ref = tool_result.get("jd_reference", "")
            finalized_at = tool_result.get("finalized_at", "")
            next_steps = tool_result.get("next_steps", [])
            parts = [f"**Status:** Finalized"]
            if ref:
                parts.append(f"**Reference:** `{ref}`")
            if finalized_at:
                parts.append(f"**Finalized at:** {finalized_at}")
            if next_steps:
                parts.append("\n**Next Steps:**")
                for step in next_steps:
                    parts.append(f"- {step}")
            elements.append(cl.Text(
                name="jd_finalized",
                content="\n".join(parts),
                display="inline",
            ))

    elif tool_name in ("jd_compose", "section_editor"):
        sections = tool_result.get("sections", {})
        if isinstance(tool_result.get("updated_content"), str):
            section_name = tool_result.get("section", "section")
            elements.append(cl.Text(
                name=f"jd_{section_name}",
                content=f"## {section_name.title()}\n\n{tool_result['updated_content']}",
                display="side",
            ))
        elif sections:
            for section_name, content in sections.items():
                elements.append(cl.Text(
                    name=f"jd_{section_name}",
                    content=f"## {section_name.title()}\n\n{content}",
                    display="side",
                ))

    return elements


ORCHESTRATOR_TOOL_NAMES = {"mycareer", "jd_generator"}


def extract_tool_calls_from_messages(messages: list) -> list[tuple[str, dict]]:
    """Extract tool name and result pairs from agent response messages.

    For orchestrator-level agent tools (``mycareer_agent``,
    ``jd_generator_agent``), the returned JSON contains a ``tool_calls``
    array with the specialist's inner tool results.  These are unwrapped so
    that ``render_tool_elements`` receives the inner tool names it expects
    (e.g. ``get_matches``, ``profile_analyzer``).
    """
    tool_calls: list[tuple[str, dict]] = []
    for msg in messages:
        if not (hasattr(msg, "type") and msg.type == "tool"):
            continue

        tool_name = getattr(msg, "name", "")
        try:
            content = msg.content
            result = json.loads(content) if isinstance(content, str) else content
        except (json.JSONDecodeError, TypeError):
            result = {"raw": str(msg.content)}

        if (
            tool_name in ORCHESTRATOR_TOOL_NAMES
            and isinstance(result, dict)
            and "tool_calls" in result
        ):
            for inner in result["tool_calls"]:
                inner_name = inner.get("name", "")
                inner_content = inner.get("content", {})
                if isinstance(inner_content, str):
                    try:
                        inner_content = json.loads(inner_content)
                    except (json.JSONDecodeError, TypeError):
                        inner_content = {"raw": inner_content}
                tool_calls.append((inner_name, inner_content))
        else:
            tool_calls.append((tool_name, result))

    return tool_calls
