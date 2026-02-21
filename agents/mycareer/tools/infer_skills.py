"""
Infer skills tool -- Mocked implementation.
"""

from typing import Any

from langchain_core.tools import tool

from core.profile import load_profile


@tool
def infer_skills() -> dict:
    """Infers and suggests relevant skills for the user based on their
    experience and education details."""
    return run_infer_skills()


def run_infer_skills() -> dict[str, Any]:
    """Actual implementation -- loads profile from the configured data path."""
    _profile = load_profile()  # noqa: F841  -- will be used once real inference is added
    top_skills = ["A2A", "MCP", "RAG"]
    additional_skills = ["Context Engineering", "Azure Open AI", "Azure AI Search"]

    return {
        "success": True,
        "error": None,
        "topSkills": top_skills,
        "additionalSkills": additional_skills,
        "evidence": [],
        "confidence": 0.75,
    }
