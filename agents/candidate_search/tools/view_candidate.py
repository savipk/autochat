"""
View a specific candidate's profile from the employee directory.
"""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.tools import tool

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "employee_directory.json")


def _load_employees() -> list[dict[str, Any]]:
    """Load employee directory from JSON."""
    with open(_DATA_PATH, "r") as f:
        data = json.load(f)
    return data.get("employees", [])


def run_view_candidate(employee_id: str) -> dict[str, Any]:
    """Look up a single employee by ID."""
    employees = _load_employees()
    for emp in employees:
        if emp.get("employeeId") == employee_id:
            return {"success": True, **emp}
    return {"success": False, "error": f"Employee '{employee_id}' not found."}


@tool
def view_candidate(employee_id: str) -> dict:
    """View detailed profile for a specific internal employee.

    Args:
        employee_id: The employee ID (e.g. "E001").

    Returns:
        Full employee record or error if not found.
    """
    return run_view_candidate(employee_id)
