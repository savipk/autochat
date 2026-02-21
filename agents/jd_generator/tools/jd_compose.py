"""
JD Compose tool -- Mocked initial JD draft generation.
"""

from langchain_core.tools import tool


@tool
def jd_compose(
    job_title: str,
    department: str,
    level: str,
    team_size: str | None = None,
    key_focus: str | None = None,
) -> dict:
    """Composes an initial job description draft with three sections:
    Summary, Responsibilities, and Qualifications. Uses similar JDs and
    corporate standards as reference."""
    return run_jd_compose(job_title, department, level, team_size, key_focus)


def run_jd_compose(
    job_title: str,
    department: str,
    level: str,
    team_size: str | None = None,
    key_focus: str | None = None,
) -> dict:
    """Actual implementation -- returns mock JD draft."""
    if not job_title or not isinstance(job_title, str):
        return {"success": False, "error": "job_title is required and must be a non-empty string."}

    if not department or not isinstance(department, str):
        return {"success": False, "error": "department is required and must be a non-empty string."}

    if not level or not isinstance(level, str):
        return {"success": False, "error": "level is required and must be a non-empty string."}

    focus = key_focus or "building innovative AI solutions"
    team = team_size or "8-12"

    return {
        "success": True,
        "error": None,
        "draft_id": "DRAFT-001",
        "title": job_title,
        "department": department,
        "level": level,
        "sections": {
            "summary": (
                f"We are seeking a {job_title} to join our {department} team. "
                f"In this {level}-level role, you will lead a team of {team} professionals "
                f"focused on {focus}. This is a high-impact position that combines technical "
                f"leadership with strategic vision to drive our AI/ML capabilities forward."
            ),
            "responsibilities": (
                f"- Lead and mentor a team of {team} engineers and data scientists\n"
                f"- Define and execute the technical strategy for {focus}\n"
                "- Collaborate with senior stakeholders to align AI initiatives with business goals\n"
                "- Design and implement scalable AI/ML solutions\n"
                "- Drive best practices in code quality, testing, and documentation\n"
                "- Present findings and recommendations to senior leadership\n"
                "- Stay current with emerging AI/ML technologies and assess applicability"
            ),
            "qualifications": (
                "- 8+ years of experience in software engineering or data science\n"
                "- 3+ years of experience leading technical teams\n"
                "- Strong expertise in Python, machine learning frameworks (PyTorch, TensorFlow)\n"
                "- Experience with cloud platforms (Azure preferred)\n"
                "- Excellent communication and stakeholder management skills\n"
                "- MS or PhD in Computer Science, Engineering, or related field preferred\n"
                "- Track record of delivering complex technical projects"
            ),
        },
        "metadata": {
            "standards_applied": True,
            "similar_jds_referenced": 2,
            "tone": "professional",
        }
    }
