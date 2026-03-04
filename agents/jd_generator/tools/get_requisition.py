"""
Get Requisition tool -- Loads job requisitions from data/job_requisitions.json.
"""

import json
import os

from langchain_core.tools import tool


@tool
def get_requisition(requisition_id: str | None = None) -> dict:
    """Retrieves open job requisitions from the system. If a requisition_id
    is provided, returns that specific requisition. Otherwise returns all
    open requisitions for the hiring manager to choose from."""
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
                return {"success": True, "requisitions": [req]}
        return {"success": False, "error": f"Requisition {requisition_id} not found."}

    # Return all open requisitions
    open_reqs = [req for req in requisitions if req.get("status") == "open"]
    if not open_reqs:
        return {"success": False, "error": "No open requisitions found."}

    return {"success": True, "requisitions": open_reqs}
