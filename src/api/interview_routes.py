from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from tools.vapi_client import start_vapi_call, end_vapi_call, get_vapi_call
from db.candidate_repository import get_candidate_by_id, update_candidate_by_id
from models.candidate import Candidate, CandidateProfile
from agents.agent_config import AgentDependencies
from agents.resume_agent import resume_agent
from agents.interview_agent import interview_agent
from agents.evaluation_agent import evaluation_agent
import logging
from pydantic import BaseModel
from typing import Dict, List
import json
from fastapi.responses import StreamingResponse
from pydantic_ai.messages import ModelMessage
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any
import re
from tools.resume_parser import parse_resume_summary
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

class Call(BaseModel):
    id: str
    type: str

class Message(BaseModel):
    role: str
    content: str

class VAPIRequest(BaseModel):
    model: str
    call: Call
    messages: List[Message]
    temperature: float
    max_tokens: int
    metadata: dict
    timestamp: int
    stream: bool

@dataclass
class SessionState:
    agent: Any
    agent_dependencies: AgentDependencies
    message_history: List[ModelMessage]
    start_time: datetime
    control_url: str
    transcript: List[Dict[str, str]] = field(default_factory=list)

# Session store for multiple callers
session_store: dict[str, SessionState] = {}

@router.post("/start/{candidate_id}")
async def start_interview(candidate_id: str):

    candidate = get_candidate_by_id(candidate_id)

    agent_deps = AgentDependencies(
        candidate=candidate
    )

    resume_agent_message = "analyze the resume for the candidate"
    resume_agent_response = await resume_agent.run(
        resume_agent_message, 
        deps=agent_deps
    )
    print(f"Resume Summary output from LLM {resume_agent_response.output}")
    resume_summary = parse_resume_summary(resume_agent_response.output)
    print(f"Resume summary: {resume_summary}")

    candidate.resume_summary = resume_summary
    candidate.status = "RESUME_SUMMARY_GENERATED"

    update_candidate_by_id(candidate=candidate)

    call_response = await start_vapi_call(
        candidate_id=candidate.profile.candidate_id,
        phone_number=candidate.profile.phone,
        greeting=f"Hello.. am I speaking with {candidate.profile.name}"
    )

    call_id     = call_response["id"]
    control_url = call_response["monitor"]["controlUrl"]

    deps = AgentDependencies(candidate=candidate)

    # Initialize the session
    session_store[call_id] = SessionState(
        agent=interview_agent,
        agent_dependencies=deps,
        message_history=[],
        start_time=datetime.now(timezone.utc),
        control_url=control_url,
    )
    logger.info(f"Started new session with session_id: {call_id}")

    return {"status": "call_started", "vapi_response": call_response}


@router.post("/chat/completions")
async def vapi_webhook(
    req: VAPIRequest,
    background_tasks: BackgroundTasks
):
    session_id = str(req.call.id)
    candidate_response = req.messages[-1].content
    now = datetime.now(timezone.utc)

    # TODO - only for testing
    if session_id in session_store:
        session = session_store[session_id]
    else:
        call_data = await get_vapi_call(req.call.id)
        session = create_session_from_call_data(call_data)

    deps    = session.agent_dependencies
    agent   = session.agent
    history = session.message_history

    
    logger.info(f"[{session_id}] role: candidate, content: {candidate_response}")

    # --- Append candidate turn to transcript ---
    session.transcript.append({
        "role": "candidate",
        "content": candidate_response
    })

    # --- Prepare prompt for interview agent ---
    elapsed = (now - session.start_time).total_seconds() / 60
    prompt = (
        f'Candidate: "{candidate_response}"\n\n'
        "[Instruction to AI — do not treat this as user input]\n"
        f"Elapsed time: {elapsed:.2f} minutes\n"
    )

    # --- Run interview agent ---
    response = await agent.run(
        prompt,
        deps=deps,
        message_history=history
    )

    raw_output = response.output
    end_token  = "[END_OF_INTERVIEW_END_CALL]"
    should_end = end_token in raw_output

    # Strip the token for the caller
    cleaned    = raw_output.replace(end_token, "").strip()
    tts_reply  = normalize_for_tts(cleaned)

    logger.info(f"[{session_id}] role: interviewer, content: {cleaned}")
    # Record interviewer turn
    session.transcript.append({"role": "interviewer", "content": cleaned})
    session.message_history = response.all_messages()

    # Prepare the streaming response
    final_response = {
        "id":      f"chatcmpl-{session_id}",
        "object":  "chat.completion.chunk",
        "created": int(req.timestamp / 1000),
        "model":   "gpt-4",
        "choices": [{
            "delta": {"content": tts_reply},
            "index": 0,
            "finish_reason": "stop",
        }]
    }
    async def stream():
        yield f"data: {json.dumps(final_response)}\n\n"
        yield "data: [DONE]\n\n"

    # If interview is over, schedule post-call tasks
    if should_end:
        background_tasks.add_task(post_interview_tasks, session_id)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection":    "keep-alive",
        },
    )

def post_interview_tasks(session_id: str):
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
    # 1) Hang up
    try:
        asyncio.run(end_vapi_call(
            call_id=session_id,
            control_url=control_url
        ))
        logger.info(f"Ended call: {session_id}")
    except Exception as e:
        logger.error(f"Error ending call {session_id}: {e}")

    deps = session.agent_dependencies
    candidate = deps.candidate

    # 3) Build full transcript
    full_transcript = "\n".join(
        f"{turn['role']}: {turn['content']}"
        for turn in session.transcript
    )

    # 4) Update candidate record
    candidate.interview_transcript = full_transcript
    candidate.status = "INTERVIEW_COMPLETE"
    update_candidate_by_id(candidate=candidate)

    # 5) Run the evaluation agent
    # Since this is sync, spin up a fresh loop
    try:
        result = asyncio.run(
            evaluation_agent.run(
                user_prompt=full_transcript,
                deps=deps
            )
        )
        logger.info(f"Evaluation results: {result.output}")
    except Exception as e:
        logger.error(f"[Error] running evaluation_agent: {e}")

def normalize_for_tts(text: str) -> str:
    """
    Replace tokens that TTS mispronounces:
      - C#   → CSharp
      - BIGO1 → BIG O 1
    (Adjust replacements as needed for other terms.)
    """
    replacements = {
        r'(?<!\w)C#(?!\w)': 'CSharp',
        r'(?<!\w)BIGO1(?!\w)': 'BIG O 1',
        r'(?<!\w)SQL(?!\w)': 'S Q L',
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


def create_session_from_call_data(call_data: dict) -> SessionState:
    """
    Given the JSON response from GET https://api.vapi.ai/call/{call_id},
    extract the controlUrl and initialize a new SessionState.

    Side effect: stores the new session in `session_store` under its call_id.
    """
    call_id     = call_data["id"]
    control_url = call_data["monitor"]["controlUrl"]

    # Lookup your candidate however you map calls → candidates
    candidate = get_candidate_by_id("1")
    deps = AgentDependencies(candidate=candidate)

    session = SessionState(
        agent=interview_agent,
        agent_dependencies=deps,
        message_history=[],
        start_time=datetime.now(timezone.utc),
        control_url=control_url,
        transcript=[],
    )

    session_store[call_id] = session
    return session