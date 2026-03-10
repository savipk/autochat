"""
Chainlit adapter -- bridges the Chainlit UI with the orchestrator agent.

Handles:
- Rendering Chainlit elements (JobCard, DraftMessage, ProfileScore) from tool results

Tool response rendering follows a prompt-driven pattern: the LLM system prompt
instructs the model not to repeat data that is shown via custom elements (e.g.
job cards, skill lists, draft message bodies).  The mapping is:

  get_matches     -> LLM intro text + JobCard elements       (LLM before elements)
  infer_skills    -> LLM intro text + SkillsCard element       (LLM before elements)
  profile_analyzer-> LLM text + ProfileScore element          (LLM before elements)
  draft_message   -> LLM text + DraftMessage element          (LLM around elements)
  send_message    -> confirmation Text element (LLM only)
  apply_for_role  -> confirmation Text element (LLM only)
  ask_jd_qa       -> LLM text + Q&A citation Text element
  update_profile  -> LLM text + profile update confirmation Text element
  get_requisition -> RequisitionCard element (LLM before element)
  jd_search       -> pass-through (panel handles display via SSE)
  jd_finalize     -> LLM text + finalization summary Text element
"""

from __future__ import annotations

import json
import logging
from typing import Any

import chainlit as cl

from core.profile_score import compute_completion_score, normalize_profile

logger = logging.getLogger("chatbot.adapter")


async def render_tool_elements(tool_name: str, tool_result: dict[str, Any]) -> list:
    """Create Chainlit elements from tool results."""
    elements: list = []

    if tool_name == "get_matches":
        matches = tool_result.get("matches", [])
        if matches:
            job_card_props: dict[str, Any] = {"jobs": matches}
            total_available = tool_result.get("total_available")
            has_more = tool_result.get("has_more")
            if total_available is not None:
                job_card_props["totalAvailable"] = total_available
            if has_more is not None:
                job_card_props["hasMore"] = has_more
            elements.append(cl.CustomElement(name="JobCard", props=job_card_props))

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
            # Load current profile skills for display
            from core.profile import load_profile
            profile = load_profile()
            normalize_profile(profile)
            core = profile.get("core", {})
            current_skills = core.get("skills") or {}
            current_top = current_skills.get("top", [])
            current_additional = current_skills.get("additional", [])
            # Normalize to name strings for the card
            current_top_names = [
                s["name"] if isinstance(s, dict) else str(s) for s in current_top
            ]
            current_additional_names = [
                s["name"] if isinstance(s, dict) else str(s) for s in current_additional
            ]

            elements.append(cl.CustomElement(name="SkillsCard", props={
                "topSkills": top,
                "additionalSkills": additional,
                "evidence": tool_result.get("evidence", []),
                "confidence": tool_result.get("confidence", 0),
                "currentTopSkills": current_top_names,
                "currentAdditionalSkills": current_additional_names,
            }))

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

            # Load current section data for before/after diff
            from core.profile import load_profile
            from core.profile_schema import resolve_section
            profile = load_profile(tool_result.get("profile_path") or None)
            core = profile.get("core", {})
            info = resolve_section(section)
            current_values = {}
            if info:
                current_values = core.get(info.storage_key, {})

            # Build payload for the action callbacks
            payload = json.dumps({
                "section": section,
                "updates": updated,
                "profile_path": tool_result.get("profile_path", ""),
                "username": tool_result.get("username", ""),
            })

            elements.append(cl.CustomElement(
                name="ProfileUpdateConfirmation",
                props={
                    "section": section,
                    "updated_fields": updated,
                    "current_values": current_values,
                    "previous_completion_score": prev_score,
                    "estimated_new_score": new_score,
                    "payload": payload,
                },
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

    elif tool_name == "get_requisition":
        reqs = tool_result.get("requisitions", [])
        if reqs:
            elements.append(cl.CustomElement(name="RequisitionCard", props={
                "requisitions": reqs,
            }))

    elif tool_name == "jd_search":
        # jd_search results are now rendered by the JD Editor side panel via SSE.
        # The panel is opened from app.py when it detects the jd_search tool call.
        pass

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
        # JD content is now rendered by the JD Editor side panel.
        # The panel is opened/refreshed via SSE events pushed from app.py.
        pass

    elif tool_name == "search_candidates":
        candidates = tool_result.get("candidates", [])
        if candidates:
            candidate_card_props: dict[str, Any] = {"candidates": candidates}
            total_available = tool_result.get("total_available")
            has_more = tool_result.get("has_more")
            if total_available is not None:
                candidate_card_props["totalAvailable"] = total_available
            if has_more is not None:
                candidate_card_props["hasMore"] = has_more
            elements.append(cl.CustomElement(name="CandidateCard", props=candidate_card_props))

    return elements


async def render_interrupt_elements(
    interrupt_data: list[dict],
    agent_name: str,
    profile_path: str,
    username: str,
) -> list:
    """Render Chainlit elements for pending human-in-the-loop interrupts.

    Currently handles ``update_profile`` interrupts by computing completion
    scores and returning a ``ProfileUpdateConfirmation`` card.
    """
    from core.profile import load_profile

    elements: list = []
    for intr in interrupt_data:
        value = intr.get("value", {})
        action_requests = value.get("action_requests", [])
        for req in action_requests:
            tool_name = req.get("name", "")
            args = req.get("args", {})

            if tool_name == "update_profile":
                section = args.get("section", "skills")
                updates = args.get("updates", {})

                # Normalize flat skills list (mirrors update_profile logic)
                if section == "skills" and "skills" in updates and isinstance(updates["skills"], list):
                    flat = updates["skills"]
                    updates = {
                        "topSkills": flat[:3],
                        "additionalSkills": flat[3:],
                    }

                # Compute before/after completion scores
                profile = load_profile(profile_path or None)
                normalize_profile(profile)
                prev_score = compute_completion_score(profile)

                simulated = _simulate_update(profile, section, updates)
                new_score = compute_completion_score(simulated)

                # Current section data for before/after diff
                from core.profile_schema import resolve_section
                core = profile.get("core", {})
                info = resolve_section(section)
                current_values = {}
                if info:
                    current_values = core.get(info.storage_key, {})

                payload = json.dumps({
                    "section": section,
                    "updates": updates,
                    "profile_path": profile_path,
                    "username": username,
                })

                elements.append(cl.CustomElement(
                    name="ProfileUpdateConfirmation",
                    props={
                        "section": section,
                        "updated_fields": updates,
                        "current_values": current_values,
                        "previous_completion_score": prev_score,
                        "estimated_new_score": new_score,
                        "payload": payload,
                    },
                ))

            elif tool_name == "rollback_profile":
                from core.profile_manager import ProfileManager

                profile = load_profile(profile_path or None)
                normalize_profile(profile)
                prev_score = compute_completion_score(profile)

                # Load most recent backup for the "proposed" side
                backup_profile = {}
                new_score = 0
                if username and profile_path:
                    mgr = ProfileManager(username=username, profile_path=profile_path)
                    backup = mgr.get_latest_backup()
                    if backup:
                        backup_profile = backup
                        normalize_profile(backup_profile)
                        new_score = compute_completion_score(backup_profile)

                # Build summary dicts for current vs backup
                current_summary = _profile_summary(profile)
                backup_summary = _profile_summary(backup_profile) if backup_profile else {}

                payload = json.dumps({
                    "section": "rollback",
                    "updates": {},
                    "profile_path": profile_path,
                    "username": username,
                })

                elements.append(cl.CustomElement(
                    name="ProfileUpdateConfirmation",
                    props={
                        "section": "rollback",
                        "updated_fields": backup_summary,
                        "current_values": current_summary,
                        "previous_completion_score": prev_score,
                        "estimated_new_score": new_score,
                        "payload": payload,
                    },
                ))

    return elements


def _profile_summary(profile: dict) -> dict:
    """Build a compact summary of key profile sections for diff display."""
    core = profile.get("core", {})
    summary: dict[str, Any] = {}

    # Experience
    exp = core.get("experience", {})
    experiences = exp.get("experiences", []) if isinstance(exp, dict) else []
    if experiences:
        summary["experience"] = [
            f"{e.get('jobTitle', '?')} at {e.get('company', '?')}"
            for e in experiences[:5]
        ]

    # Skills
    skills = core.get("skills", {})
    if isinstance(skills, dict):
        top = skills.get("top", [])
        additional = skills.get("additional", [])
        top_names = [s["name"] if isinstance(s, dict) else str(s) for s in top]
        add_names = [s["name"] if isinstance(s, dict) else str(s) for s in additional]
        if top_names or add_names:
            summary["skills"] = {"top": top_names, "additional": add_names}

    # Education
    qual = core.get("qualification", {})
    educations = qual.get("educations", []) if isinstance(qual, dict) else []
    if educations:
        summary["education"] = [
            f"{e.get('degree', '?')} at {e.get('institutionName', '?')}"
            for e in educations[:5]
        ]

    return summary


def _simulate_update(profile: dict, section: str, updates: dict) -> dict:
    """Return a copy of *profile* with *updates* applied (without persisting).

    Uses the schema registry to resolve storage keys so that aliases
    (e.g. ``education`` → ``qualification``) are handled correctly.
    """
    import copy
    from core.profile_schema import resolve_section

    sim = copy.deepcopy(profile)
    normalize_profile(sim)
    core = sim.setdefault("core", {})
    info = resolve_section(section)
    storage_key = info.storage_key if info else section

    if section == "skills":
        if core.get("skills") is None:
            core["skills"] = {}
        core.setdefault("skills", {})
        if "topSkills" in updates:
            core["skills"]["top"] = updates["topSkills"]
        if "additionalSkills" in updates:
            core["skills"]["additional"] = updates["additionalSkills"]
    elif info and info.list_field and info.list_field in updates:
        # Merge new list entries into existing
        existing = core.get(storage_key, {})
        existing_items = existing.get(info.list_field, []) if isinstance(existing, dict) else []
        new_items = updates[info.list_field]
        if isinstance(new_items, list):
            existing.setdefault(info.list_field, [])
            existing[info.list_field] = existing_items + new_items
        core[storage_key] = existing
    else:
        core[storage_key] = updates
    return sim


ORCHESTRATOR_TOOL_NAMES = {"profile", "job_discovery", "outreach", "candidate_search", "jd_generator"}


def extract_tool_calls_from_messages(messages: list) -> list[tuple[str, dict]]:
    """Extract tool name and result pairs from agent response messages.

    For orchestrator-level agent tools (``profile_agent``,
    ``job_discovery_agent``, ``outreach_agent``, ``candidate_search_agent``,
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


def extract_interrupts_from_messages(messages: list) -> list[dict]:
    """Extract interrupt payloads from orchestrator worker agent results.

    When a worker agent hits a ``HumanInTheLoopMiddleware`` interrupt the
    returned JSON contains an ``interrupts`` key instead of ``tool_calls``.
    """
    interrupts: list[dict] = []
    for msg in messages:
        if not (hasattr(msg, "type") and msg.type == "tool"):
            continue
        tool_name = getattr(msg, "name", "")
        if tool_name not in ORCHESTRATOR_TOOL_NAMES:
            continue
        try:
            content = msg.content
            result = json.loads(content) if isinstance(content, str) else content
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(result, dict) and "interrupts" in result:
            for intr in result["interrupts"]:
                interrupts.append({
                    "interrupt": intr,
                    "agent_name": result.get("agent_name", tool_name),
                })
    return interrupts
