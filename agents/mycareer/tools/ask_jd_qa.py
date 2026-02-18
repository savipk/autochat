"""
Ask JD Q&A tool -- Mocked implementation with two scenarios.
Copied AS IS from tpchat/src/tools.py.
"""

from langchain_core.tools import tool


@tool
def ask_jd_qa(job_id: str, question: str) -> dict:
    """Answers questions about a specific job posting based on the job
    description and available details."""
    return run_ask_jd_qa(job_id, question)


def run_ask_jd_qa(job_id: str, question: str) -> dict:
    """Actual implementation."""
    question_lower = question.lower()

    job_context = {
        "job_id": job_id or "331525BR",
        "job_title": "GenAI Lead",
        "hiring_manager": "Prasanth Jagannathan",
        "org_line": "GWM COO Americas",
        "location": "United States",
        "level": "Executive Director"
    }

    # Scenario 1: Team size question -- has answer
    team_keywords = [
        "team size", "how many people", "how big is the team",
        "team members", "people on the team", "size of the team"
    ]
    is_team_question = (
        any(kw in question_lower for kw in team_keywords)
        or ("team" in question_lower and ("size" in question_lower or "how many" in question_lower or "members" in question_lower))
    )

    if is_team_question:
        return {
            "answer": "Lead a team of 10-15 highly capable data scientists focused on building impactful AI applications.",
            "answer_found": True,
            "citations": ["Job posting - Team section"],
            "confidence": 0.90,
            "job_id": job_context["job_id"],
            "job_title": job_context["job_title"],
            "hiring_manager": job_context["hiring_manager"],
            "success": True
        }

    # Scenario 2: Project focus question -- no specific answer
    project_keywords = [
        "project", "focus", "work on", "working on",
        "what will i be doing", "responsibilities", "what does this role"
    ]
    is_project_question = any(kw in question_lower for kw in project_keywords)

    if is_project_question:
        return {
            "answer": "building impactful AI applications",
            "answer_found": False,
            "partial_context": "building impactful AI applications",
            "citations": [],
            "confidence": 0.30,
            "job_id": job_context["job_id"],
            "job_title": job_context["job_title"],
            "hiring_manager": job_context["hiring_manager"],
            "org_line": job_context["org_line"],
            "success": True,
            "suggest_contact_hiring_manager": True
        }

    # Default: Generic response
    return {
        "answer": f"Based on the job posting for {job_context['job_title']}, this is an {job_context['level']} role in {job_context['org_line']}.",
        "answer_found": True,
        "citations": ["Job posting - General information"],
        "confidence": 0.75,
        "job_id": job_context["job_id"],
        "job_title": job_context["job_title"],
        "hiring_manager": job_context["hiring_manager"],
        "success": True
    }
