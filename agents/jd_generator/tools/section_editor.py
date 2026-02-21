"""
Section editor tool -- Edits a specific section of a JD draft.
"""

from langchain_core.tools import tool

VALID_SECTIONS = ["summary", "responsibilities", "qualifications"]


@tool
def section_editor(
    draft_id: str,
    section: str,
    instruction: str,
) -> dict:
    """Edits a specific section (summary, responsibilities, or qualifications)
    of a JD draft based on the user's feedback or instructions."""
    return run_section_editor(draft_id, section, instruction)


def run_section_editor(
    draft_id: str,
    section: str,
    instruction: str,
) -> dict:
    """Actual implementation -- returns mock edited section."""
    if not draft_id or not isinstance(draft_id, str):
        return {"success": False, "error": "draft_id is required and must be a non-empty string."}

    if not instruction or not isinstance(instruction, str):
        return {"success": False, "error": "instruction is required and must be a non-empty string."}

    if not section or section.lower() not in VALID_SECTIONS:
        return {
            "success": False,
            "error": f"Invalid section '{section}'. Must be one of: {VALID_SECTIONS}",
        }

    mock_edits = {
        "summary": (
            "We are seeking a visionary GenAI Lead to spearhead our "
            "Technology division's AI transformation. In this Executive Director-level "
            "role, you will lead a team of 10-15 professionals focused on building "
            "next-generation AI applications that drive measurable business impact."
        ),
        "responsibilities": (
            "- Lead and grow a high-performing team of 10-15 AI engineers and data scientists\n"
            "- Define the strategic roadmap for generative AI adoption across the firm\n"
            "- Architect and deliver production-grade AI/ML solutions\n"
            "- Partner with business leaders to identify high-value AI use cases\n"
            "- Establish engineering excellence standards and best practices\n"
            "- Manage vendor relationships and evaluate emerging AI technologies\n"
            "- Present technical strategy to C-suite and senior leadership"
        ),
        "qualifications": (
            "- 10+ years in software engineering with 5+ years in AI/ML\n"
            "- 4+ years leading technical teams of 8+ people\n"
            "- Deep expertise in LLMs, RAG, and generative AI architectures\n"
            "- Hands-on experience with Azure OpenAI, LangChain, or similar frameworks\n"
            "- Strong experience with cloud platforms (Azure strongly preferred)\n"
            "- Exceptional communication skills with executive presence\n"
            "- MS or PhD in Computer Science, AI/ML, or related field"
        ),
    }

    return {
        "success": True,
        "error": None,
        "draft_id": draft_id,
        "section": section.lower(),
        "instruction_applied": instruction,
        "updated_content": mock_edits.get(section.lower(), "Section updated based on your instructions."),
        "revision_number": 2,
    }
