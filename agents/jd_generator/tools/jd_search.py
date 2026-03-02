"""
JD Search tool -- Mocked RAG search for similar past job descriptions.
"""

from langchain_core.tools import tool


@tool
def jd_search(job_title: str, department: str | None = None) -> dict:
    """Searches for similar past job descriptions via RAG to use as references
    when composing a new JD."""
    return run_jd_search(job_title, department)


def run_jd_search(job_title: str, department: str | None = None) -> dict:
    """Actual implementation -- returns mock similar JDs."""
    if not job_title or not isinstance(job_title, str):
        return {"success": False, "error": "job_title is required and must be a non-empty string."}

    return {
        "success": True,
        "error": None,
        "count": 2,
        "similar_jds": [
            {
                "id": "JD-2024-001",
                "title": "Senior Data Scientist",
                "department": department or "Technology",
                "level": "Vice President",
                "similarity_score": 0.89,
                "summary": "Lead a team of data scientists building ML models for risk analytics.",
                "sections": {
                    "your_team": "Join our risk analytics group, a team of 5-8 data scientists building ML models that power firm-wide risk decisions.",
                    "your_role": "- Lead a team of 5-8 data scientists\n- Design and implement ML models\n- Collaborate with stakeholders to define requirements\n- Mentor junior team members",
                    "your_expertise": "- 8+ years of experience in data science\n- PhD or MS in Computer Science, Statistics, or related field\n- Strong experience with Python, TensorFlow, PyTorch\n- Experience leading technical teams"
                }
            },
            {
                "id": "JD-2024-002",
                "title": "AI/ML Engineering Lead",
                "department": department or "Technology",
                "level": "Executive Director",
                "similarity_score": 0.82,
                "summary": "Drive the development of AI/ML infrastructure and lead engineering team.",
                "sections": {
                    "your_team": "Our AI/ML engineering team of 10+ engineers is building the next-generation AI platform that powers intelligent solutions across the firm.",
                    "your_role": "- Architect and build scalable ML infrastructure\n- Lead a team of 10+ engineers\n- Define technical roadmap\n- Partner with product teams on AI features",
                    "your_expertise": "- 10+ years in software engineering, 5+ in ML\n- Experience with cloud platforms (AWS/Azure/GCP)\n- Strong leadership and communication skills\n- Track record of delivering ML systems at scale"
                }
            }
        ]
    }
