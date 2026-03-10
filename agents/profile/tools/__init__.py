from agents.shared.tools.profile_analyzer import profile_analyzer
from agents.shared.tools.update_profile import update_profile
from agents.shared.tools.infer_skills import infer_skills
from agents.shared.tools.list_profile_entries import list_profile_entries
from agents.shared.tools.open_profile_panel import open_profile_panel
from agents.shared.tools.rollback_profile import rollback_profile

PROFILE_TOOLS = [
    profile_analyzer,
    update_profile,
    infer_skills,
    list_profile_entries,
    open_profile_panel,
    rollback_profile,
]
