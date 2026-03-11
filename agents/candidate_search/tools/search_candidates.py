"""
Search the internal employee directory for candidates matching criteria.
"""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.tools import tool

_DATA_PATH = os.path.normpath(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "employee_directory.json")
))


def _load_employees() -> list[dict[str, Any]]:
    """Load employee directory from JSON."""
    with open(_DATA_PATH, "r") as f:
        data = json.load(f)
    return data.get("employees", [])


def _score_candidate(
    employee: dict[str, Any],
    search_words: list[str],
    filter_skills: list[str],
) -> int:
    """Score a candidate based on skills overlap, search term hits, and profile completeness.

    Scoring algorithm:
    - Skills overlap: 10 pts per matching skill (case-insensitive)
    - Search term hits: 5 pts per keyword hit across name/title/department/skills
    - Profile completeness bonus: x1.1 multiplier if profileCompletionScore >= 80
    """
    score = 0

    emp_skills_lower = [s.lower() for s in employee.get("skills", [])]

    # Skills overlap scoring
    for skill in filter_skills:
        if skill.lower() in emp_skills_lower:
            score += 10

    # Search term hits
    searchable_text = " ".join([
        employee.get("name", ""),
        employee.get("businessTitle", ""),
        employee.get("department", ""),
        " ".join(employee.get("skills", [])),
        employee.get("location", ""),
    ]).lower()

    for word in search_words:
        if word.lower() in searchable_text:
            score += 5

    # Profile completeness bonus
    if employee.get("profileCompletionScore", 0) >= 80:
        score = int(score * 1.1)

    return score


def _matches_filters(employee: dict[str, Any], filters: dict[str, Any]) -> bool:
    """Check if an employee matches all provided filters (AND logic)."""
    if "country" in filters:
        if filters["country"].lower() not in employee.get("country", "").lower():
            return False

    if "location" in filters:
        if filters["location"].lower() not in employee.get("location", "").lower():
            return False

    if "department" in filters:
        if filters["department"].lower() not in employee.get("department", "").lower():
            return False

    level = filters.get("level") or filters.get("rank")
    if level:
        rank = employee.get("rank", {})
        rank_code = rank.get("code", "") if isinstance(rank, dict) else str(rank)
        if rank_code.upper() != level.upper():
            return False

    if "skills" in filters:
        filter_skills = filters["skills"]
        if isinstance(filter_skills, list) and filter_skills:
            emp_skills_lower = {s.lower() for s in employee.get("skills", [])}
            if not any(s.lower() in emp_skills_lower for s in filter_skills):
                return False

    if "minScore" in filters:
        if employee.get("profileCompletionScore", 0) < filters["minScore"]:
            return False

    return True


def run_search_candidates(
    search_text: str = "",
    filters: dict[str, Any] | None = None,
    top_k: int = 5,
    offset: int = 0,
) -> dict[str, Any]:
    """Search the employee directory and return scored, ranked results."""
    employees = _load_employees()
    filters = filters or {}

    # Parse search words
    search_words = search_text.split() if search_text else []

    # Extract skills from filters for scoring
    filter_skills = filters.get("skills", []) if isinstance(filters.get("skills"), list) else []

    # Filter candidates
    matched = []
    for emp in employees:
        if not _matches_filters(emp, filters):
            continue

        # If search_text provided, check all words appear somewhere
        if search_words:
            searchable = " ".join([
                emp.get("name", ""),
                emp.get("businessTitle", ""),
                emp.get("department", ""),
                " ".join(emp.get("skills", [])),
                emp.get("location", ""),
            ]).lower()
            if not all(w.lower() in searchable for w in search_words):
                continue

        score = _score_candidate(emp, search_words, filter_skills)
        matched.append({**emp, "matchScore": score})

    # Sort by score descending, then by name
    matched.sort(key=lambda x: (-x["matchScore"], x.get("name", "")))

    total_available = len(matched)
    page = matched[offset:offset + top_k]
    has_more = (offset + top_k) < total_available

    return {
        "success": True,
        "candidates": page,
        "count": len(page),
        "total_available": total_available,
        "has_more": has_more,
        "filters_applied": filters,
        "search_text_used": search_text,
    }


@tool
def search_candidates(
    search_text: str = "",
    filters: dict[str, Any] | None = None,
    top_k: int = 5,
    offset: int = 0,
) -> dict:
    """Search internal employee directory for candidates by skills, level, location, and department.

    Args:
        search_text: Free-text search (AND logic across name, title, department, skills, location).
        filters: Dict with optional keys: country, location, department, level/rank, skills (list), minScore.
        top_k: Maximum results to return (default 5).
        offset: Pagination offset for "show more" (default 0).

    Returns:
        Dict with success, candidates, count, total_available, has_more, filters_applied.
    """
    return run_search_candidates(
        search_text=search_text,
        filters=filters,
        top_k=top_k,
        offset=offset,
    )
