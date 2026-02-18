"""
Chainlit adapter -- bridges the Chainlit UI with the concierge agent.

Handles:
- Streaming agent responses to the chat
- Rendering Chainlit elements (JobCard, DraftMessage, ProfileScore) from tool results
- Managing TaskList for JD Composer workflow
"""

from __future__ import annotations

import json
import logging
from typing import Any

import chainlit as cl

logger = logging.getLogger("autochat.adapter")


async def render_tool_elements(tool_name: str, tool_result: dict[str, Any]) -> list:
    """Create Chainlit elements from tool results."""
    elements = []

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


def extract_tool_calls_from_messages(messages: list) -> list[tuple[str, dict]]:
    """Extract tool name and result pairs from agent response messages."""
    tool_calls = []
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "tool":
            tool_name = getattr(msg, "name", "")
            try:
                content = msg.content
                if isinstance(content, str):
                    result = json.loads(content)
                else:
                    result = content
            except (json.JSONDecodeError, TypeError):
                result = {"raw": str(msg.content)}
            tool_calls.append((tool_name, result))
    return tool_calls


async def create_jd_task_list(status: str = "Starting...") -> cl.TaskList:
    """Create a TaskList for JD Composer workflow."""
    task_list = cl.TaskList()
    task_list.status = status

    task1 = cl.Task(title="Gather job requirements", status=cl.TaskStatus.READY)
    task2 = cl.Task(title="Search similar JDs", status=cl.TaskStatus.READY)
    task3 = cl.Task(title="Load JD standards", status=cl.TaskStatus.READY)
    task4 = cl.Task(title="Compose initial draft", status=cl.TaskStatus.READY)
    task5 = cl.Task(title="Review and iterate", status=cl.TaskStatus.READY)
    task6 = cl.Task(title="Finalize JD", status=cl.TaskStatus.READY)

    await task_list.add_task(task1)
    await task_list.add_task(task2)
    await task_list.add_task(task3)
    await task_list.add_task(task4)
    await task_list.add_task(task5)
    await task_list.add_task(task6)

    return task_list
