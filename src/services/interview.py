import logging
from datetime import datetime, timezone

from agents.interview_agent import interview_agent
from db.candidate_repository import get_candidate_by_id
from models.agent_dependencies import AgentDependencies
from models.session_state import SessionState, session_store
from tools.vapi_client import start_vapi_call

logger = logging.getLogger(__name__)


async def run_interview(candidate_id: str):
    candidate = get_candidate_by_id(candidate_id)

    # commented for real interviews
    # agent_deps = AgentDependencies(candidate=candidate)

    # resume_agent_message = "analyze the resume for the candidate"
    # resume_agent_response = await resume_agent.run(
    #     resume_agent_message,
    #     deps=agent_deps
    # )
    # logger.info(f"Resume Summary output from LLM {resume_agent_response.output}")

    # resume_summary = parse_resume_summary(resume_agent_response.output)
    # logger.info(f"Resume summary: {resume_summary}")

    # candidate.resume_summary = resume_summary
    # candidate.status = "RESUME_SUMMARY_GENERATED"
    # update_candidate_by_id(candidate=candidate)

    call_response = await start_vapi_call(
        candidate_id=candidate.profile.candidate_id,
        phone_number=candidate.profile.phone,
        greeting=f"Hello.. am I speaking with {candidate.profile.name}",
    )

    call_id = call_response["id"]
    control_url = call_response["monitor"]["controlUrl"]

    deps = AgentDependencies(candidate=candidate)

    session_store[call_id] = SessionState(
        agent=interview_agent,
        agent_dependencies=deps,
        message_history=[],
        start_time=datetime.now(timezone.utc),
        control_url=control_url,
    )

    logger.info(f"Started new session with session_id: {call_id}")

    return {"status": "call_started", "vapi_response": call_response}
