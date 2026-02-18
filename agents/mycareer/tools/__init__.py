from agents.mycareer.tools.profile_analyzer import profile_analyzer, run_profile_analyzer
from agents.mycareer.tools.update_profile import update_profile, run_update_profile
from agents.mycareer.tools.infer_skills import infer_skills, run_infer_skills
from agents.mycareer.tools.get_matches import get_matches, run_get_matches
from agents.mycareer.tools.ask_jd_qa import ask_jd_qa, run_ask_jd_qa
from agents.mycareer.tools.draft_message import draft_message, run_draft_message
from agents.mycareer.tools.send_message import send_message, run_send_message
from agents.mycareer.tools.apply_for_role import apply_for_role, run_apply_for_role

ALL_TOOLS = [
    profile_analyzer,
    update_profile,
    infer_skills,
    get_matches,
    ask_jd_qa,
    draft_message,
    send_message,
    apply_for_role,
]
