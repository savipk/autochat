"""
Infer skills tool -- Mocked implementation.
Copied AS IS from tpchat/src/tools.py.
"""

from typing import Any

from langchain_core.tools import tool


@tool
def infer_skills() -> dict:
    """Infers and suggests relevant skills for the user based on their
    experience and education details."""
    return run_infer_skills({})


def run_infer_skills(profile: dict[str, Any]) -> dict[str, Any]:
    """Actual implementation."""
    top_skills = ["A2A", "MCP", "RAG"]
    additional_skills = ["Context Engineering", "Azure Open AI", "Azure AI Search"]

    return {
        "topSkills": top_skills,
        "additionalSkills": additional_skills,
        "evidence": [],
        "confidence": 0.75,
        "success": True
    }
