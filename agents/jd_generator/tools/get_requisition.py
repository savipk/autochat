"""
Get Requisition tool -- Loads job requisitions from data/job_requisitions.json.
"""

import json
import os

from langchain_core.tools import tool


@tool
def get_requisition(requisition_id: str | None = None) -> dict:
    """Retrieves an open job requisition from the system. If no requisition_id
    is provided, returns the first open requisition."""
    return run_get_requisition(requisition_id)


def run_get_requisition(requisition_id: str | None = None) -> dict:
    """Actual implementation -- loads from data/job_requisitions.json."""
    data_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "job_requisitions.json")
    data_path = os.path.normpath(data_path)

    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"success": False, "error": "Job requisitions data file not found."}
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid job requisitions data file."}

    requisitions = data.get("requisitions", [])
    if not requisitions:
        return {"success": False, "error": "No requisitions found in the system."}

    if requisition_id:
        for req in requisitions:
            if req.get("requisition_id") == requisition_id:
                return {"success": True, "requisition": req}
        return {"success": False, "error": f"Requisition {requisition_id} not found."}

    # Return first open requisition
    for req in requisitions:
        if req.get("status") == "open":
            return {"success": True, "requisition": req}

    return {"success": False, "error": "No open requisitions found."}
