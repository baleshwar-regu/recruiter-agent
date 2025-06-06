import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic_ai.usage import Usage

from agents.agent_cost import compute_llm_cost
from agents.evaluation_agent import evaluation_agent
from agents.interview_agent import interview_agent
from config import (
    CALENDLY_MEETING_URL,
    CANDIDATE_ID_TESTING,
    EVALUATION_LLM_MODEL,
    INTERVIEW_LLM_MODEL,
    RESUME_LLM_MODEL,
)
from db.candidate_repository import get_candidate_by_id, update_candidate_by_id
from models.agent_dependencies import AgentDependencies
from models.llm_cost import AgentLLMCost
from models.session_state import SessionState, session_store
from models.vapi_request import VAPIRequest
from services.interview import run_interview
from tools.calendly_handler import dispatch_event, extract_event_id
from tools.scheduler import (
    cancel_interview,
    schedule_interview,
    scheduler,
    start_scheduler,
)
from tools.vapi_client import end_vapi_call, get_vapi_call

logger = logging.getLogger(__name__)

router = APIRouter()
start_scheduler()


def parse_agent_output(raw_output: str):
    try:
        response = json.loads(raw_output)
        agent_response = response.get("agent_response", "").strip()
        turn_outcome = response.get("turn_outcome", "").strip().upper()
        turn_outcome_reasoning = response.get("turn_outcome_reasoning", "").strip()

        valid_outcomes = {
            "NORMAL",
            "WRAP_UP",
            "GATEKEEPER_FAILURE_ALREADY_INTERVIEWED",
            "GATEKEEPER_FAILURE_INOFFICE_NOTPOSSIBLE",
            "CANDIDATE_REQUESTING_END_CALL",
        }

        if not agent_response:
            agent_response = "I couldn't quite get that, please repeat what you said.."

        if turn_outcome not in valid_outcomes:
            turn_outcome = "NORMAL"

        if not turn_outcome_reasoning:
            turn_outcome_reasoning = "NO_TURN_OUTCOME_REASONING_PROVIDED"

        should_end = turn_outcome in {
            "GATEKEEPER_FAILURE_ALREADY_INTERVIEWED",
            "GATEKEEPER_FAILURE_INOFFICE_NOTPOSSIBLE",
            "CANDIDATE_REQUESTING_END_CALL",
            "WRAP_UP",
        }

        # Override final agent response if it's a known terminal state
        if turn_outcome == "GATEKEEPER_FAILURE_ALREADY_INTERVIEWED":
            agent_response = (
                "I appreciate you letting me know. Since you've already interviewed with the client, "
                "I don't want to duplicate efforts. Thank you for your time today—I'll close us out here."
            )
        elif turn_outcome == "GATEKEEPER_FAILURE_INOFFICE_NOTPOSSIBLE":
            agent_response = (
                "Thanks for being upfront. Client has a strict three-day in-office policy, "
                "so this role wouldn't be a fit. I'll wrap up our call now, and we'll keep you in mind "
                "for other opportunities. Take care!"
            )

        return agent_response, turn_outcome, turn_outcome_reasoning, should_end

    except json.JSONDecodeError:
        return (
            "I couldn't quite get that, please repeat what you said..",
            "NORMAL",
            False,
        )


@router.get("/healthz")
def health_check():
    return {"status": "ok"}


@router.post("/calendly-webhook")
async def calendly_webhook(request: Request):
    body = await request.json()
    event_type = body.get("event")

    interview_meeting_url = (
        body.get("payload", {}).get("scheduled_event", {}).get("event_type")
    )

    # only proceed if meeting is for interview
    if interview_meeting_url != CALENDLY_MEETING_URL:
        logging.info("Received calendly event for a different meeting")
        return {"status": "ok"}

    payload = body.get("payload", {})
    event_url = payload.get("event")
    event = extract_event_id(event_url)
    logger.info(f"Incoming Calendly event_type: {event_type} event: {event}")

    try:
        result = dispatch_event(event_type, payload)
        candidate_id = result["candidate_id"]

        if event_type == "invitee.created":
            schedule_interview(candidate_id, event, result["scheduled_time"])
        elif event_type == "invitee.canceled":
            cancel_interview(candidate_id, event)

        return {"status": result["status"], "candidate_id": candidate_id}

    except Exception as e:
        logger.exception(f"[Webhook Error] {e}")
        raise HTTPException(
            status_code=500, detail="Calendly webhook failed to process"
        )


@router.post("/vapi-webhook")
async def vapi_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    message = body.get("message", {})

    status = message.get("status")
    call_id = message.get("call", {}).get("id")
    reason = message.get("endedReason")

    logger.info(f"[VAPI Webhook] Call: {call_id}, status: {status}, reason: {reason}")
    if status == "ended" and reason != "assistant-ended-call-after-message-spoken":
        background_tasks.add_task(post_interview_tasks, call_id, False)

    return {"status": "ok"}


@router.post("/start/{candidate_id}")
async def start_interview(candidate_id: str):
    return await run_interview(candidate_id)

@router.post("/evaluate/{candidate_id}")
async def evaluate_interview(candidate_id: str):
    logger.info(f"[ADHOC_RUN] Starting evaluation for candidate: {candidate_id}")
    candidate = get_candidate_by_id(candidate_id)
    deps = AgentDependencies(candidate=candidate)
    full_transcript = candidate.interview_transcript
    logger.info(f"Transcript: {full_transcript}")
    evaluation_agent_usage = Usage()
    try:
        result = await evaluation_agent.run(
            user_prompt=full_transcript, usage=evaluation_agent_usage, deps=deps
        )
        logger.info(f"[ADHOC_RUN] Evaluation results: {candidate.evaluation}")
    except Exception as e:
        logger.error(f"[ADHOC_RUN] [Error] running evaluation_agent: {e}")
    
    evaluation_agent_cost = await compute_llm_cost(
        evaluation_agent_usage, EVALUATION_LLM_MODEL
    )

    agent_llm_cost = AgentLLMCost(
        evaluation_agent=evaluation_agent_cost,
    )

    total_llm_cost = agent_llm_cost.total_llm_cost()

    candidate.llm_cost = total_llm_cost
    candidate.agent_llm_cost = agent_llm_cost
    logger.info(f"[ADHOC_RUN] Total interview cost {total_llm_cost}")
    update_candidate_by_id(candidate=candidate)

    return {"status": "ok"}



@router.post("/chat/completions")
async def vapi_chat_completions(req: VAPIRequest, background_tasks: BackgroundTasks):
    session_id = str(req.call.id)
    candidate_response = req.messages[-1].content

    # only for testing
    if session_id in session_store:
        session = session_store[session_id]
    else:
        call_data = await get_vapi_call(req.call.id)
        session = create_session_from_call_data(call_data)

    now = datetime.now(timezone.utc)
    deps = session.agent_dependencies
    agent = session.agent
    history = session.message_history
    interview_agent_usage = session.interview_agent_usage

    logger.info(f"[{session_id}] role: candidate, content: {candidate_response}")

    # --- Append candidate turn to transcript ---
    session.transcript.append({"role": "candidate", "content": candidate_response})

    candidate_intro = (
        f"Candidate profile: {deps.candidate.profile}\n"
        f"Resume summary: {deps.candidate.resume_summary}"
    )

    prompt = ""

    if not history:
        prompt += candidate_intro + "\n"

    prompt += f'Candidate: "{candidate_response}"'

    # --- Run interview agent ---
    response = await agent.run(
        user_prompt=prompt,
        deps=deps,
        usage=interview_agent_usage,
        message_history=history,
    )
    raw_output = response.output

    agent_response, turn_outcome, turn_outcome_reasoning, should_end = (
        parse_agent_output(raw_output)
    )

    tts_reply = normalize_for_tts(agent_response)
    logger.info(
        f"[{session_id}] role: interviewer, turn_outcome: {turn_outcome}, turn_outcome_reasoning: {turn_outcome_reasoning}, content: {tts_reply}"
    )
    # Record interviewer turn
    session.transcript.append({"role": "interviewer", "content": agent_response})

    session.message_history = response.all_messages()

    # Prepare the streaming response
    final_response = {
        "id": f"chatcmpl-{session_id}",
        "object": "chat.completion.chunk",
        "created": int(req.timestamp / 1000),
        "model": INTERVIEW_LLM_MODEL,
        "choices": [
            {
                "delta": {"content": tts_reply},
                "index": 0,
                "finish_reason": "stop",
            }
        ],
    }

    async def stream():
        yield f"data: {json.dumps(final_response)}\n\n"
        yield "data: [DONE]\n\n"
        # If interview is over, schedule post-call tasks
        # session_end_call helps to end the call only once
        if should_end and not session.end_call:
            session.end_call = True
            background_tasks.add_task(post_interview_tasks, session_id, True)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/scheduled-interviews", response_model=List[dict])
def list_scheduled_jobs():
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append(
            {
                "job_id": job.id,
                "next_run_time": (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
                "name": job.name,
            }
        )
    return jobs_info


@router.delete("/scheduled-interviews/{job_id}")
def delete_scheduled_job(job_id: str):
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404, detail=f"No scheduled job with id: {job_id}"
        )

    scheduler.remove_job(job_id)
    return {"message": f"Job {job_id} successfully deleted"}


async def post_interview_tasks(session_id: str, end_call: bool = True):
    """
    Background task to run after the HTTP response is sent.
    1. Hang up the VAPI call
    2. Build transcript, update candidate, run evaluation
    """
    session = session_store.get(session_id)
    if not session:
        logger.error(f"[Error] no session for {session_id}")
        return

    control_url = session.control_url
    # only end_call if not initiated by caller
    if end_call:
        try:
            logger.info(f"[{session_id}] Waiting 30s before ending call...")
            await asyncio.sleep(30)
            await end_vapi_call(call_id=session_id, control_url=control_url)
            logger.info(f"Ended call: {session_id}")
        except Exception as e:
            logger.error(f"Error ending call {session_id}: {e}")

    deps = session.agent_dependencies
    evaluation_agent_usage = session.evaluation_agent_usage
    candidate = deps.candidate

    # 3) Build full transcript
    full_transcript = "\n".join(
        f"{turn['role']}: {turn['content']}" for turn in session.transcript
    )

    # 4) Update candidate record
    candidate.interview_transcript = full_transcript
    candidate.status = "INTERVIEW_COMPLETE"
    update_candidate_by_id(candidate=candidate)

    # 5) Run the evaluation agent
    # Since this is sync, spin up a fresh loop
    try:
        result = await evaluation_agent.run(
            user_prompt=full_transcript, usage=evaluation_agent_usage, deps=deps
        )
        logger.info(f"[{session_id}] Evaluation results: {candidate.evaluation}")
    except Exception as e:
        logger.error(f"[{session_id}] [Error] running evaluation_agent: {e}")

    resume_agent_cost = await compute_llm_cost(
        session.resume_agent_usage, RESUME_LLM_MODEL
    )
    interview_agent_cost = await compute_llm_cost(
        session.interview_agent_usage, INTERVIEW_LLM_MODEL
    )
    evaluation_agent_cost = await compute_llm_cost(
        session.evaluation_agent_usage, EVALUATION_LLM_MODEL
    )

    agent_llm_cost = AgentLLMCost(
        resume_agent=resume_agent_cost,
        interview_agent=interview_agent_cost,
        evaluation_agent=evaluation_agent_cost,
    )

    total_llm_cost = agent_llm_cost.total_llm_cost()

    candidate.llm_cost = total_llm_cost
    candidate.agent_llm_cost = agent_llm_cost
    logger.info(f"[{session_id}] Total interview cost {total_llm_cost}")
    update_candidate_by_id(candidate=candidate)


def normalize_for_tts(text: str) -> str:
    """
    Replace tokens that TTS mispronounces:
      - C#   → CSharp
      - BIGO1 → BIG O 1
    (Adjust replacements as needed for other terms.)
    """
    replacements = {
        r"(?<!\w)C#(?!\w)": "CSharp",
        r"(?<!\w)BIGO1(?!\w)": "BIG O 1",
        r"(?<!\w)SQL(?!\w)": "S Q L",
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


# called during an adhoc test
def create_session_from_call_data(call_data: dict) -> SessionState:
    """
    Given the JSON response from GET https://api.vapi.ai/call/{call_id},
    extract the controlUrl and initialize a new SessionState.

    Side effect: stores the new session in `session_store` under its call_id.
    """
    call_id = call_data["id"]
    control_url = call_data["monitor"]["controlUrl"]

    candidate = get_candidate_by_id(CANDIDATE_ID_TESTING)
    deps = AgentDependencies(candidate=candidate)

    session = SessionState(
        agent=interview_agent,
        agent_dependencies=deps,
        resume_agent_usage=Usage(),
        interview_agent_usage=Usage(),
        evaluation_agent_usage=Usage(),
        message_history=[],
        start_time=datetime.now(timezone.utc),
        control_url=control_url,
        transcript=[],
    )

    session_store[call_id] = session
    return session
