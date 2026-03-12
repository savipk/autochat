from agents.shared.tools.profile_analyzer import profile_analyzer, run_profile_analyzer
from agents.shared.tools.update_profile import update_profile, run_update_profile
from agents.shared.tools.infer_skills import infer_skills, run_infer_skills
from agents.shared.tools.get_matches import get_matches, run_get_matches
from agents.shared.tools.ask_jd_qa import ask_jd_qa, run_ask_jd_qa
from agents.shared.tools.draft_message import draft_message, run_draft_message
from agents.shared.tools.send_message import send_message, run_send_message
from agents.shared.tools.open_profile_panel import open_profile_panel, run_open_profile_panel
from agents.shared.tools.view_job import view_job, run_view_job
from agents.shared.tools.list_profile_entries import list_profile_entries, run_list_profile_entries
from agents.shared.tools.rollback_profile import rollback_profile, run_rollback_profile

ALL_TOOLS = [
    profile_analyzer,
    update_profile,
    infer_skills,
    get_matches,
    ask_jd_qa,
    draft_message,
    send_message,
    open_profile_panel,
    view_job,
    list_profile_entries,
    rollback_profile,
]
