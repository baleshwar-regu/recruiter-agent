from fastapi import APIRouter, Request
from pydantic import BaseModel
from tools.vapi_client import start_vapi_call
from db.candidate_repository import get_candidate_by_id, update_candidate_by_id
from models.candidate import Candidate, CandidateProfile
from agents.agent_config import AgentDependencies
from agents.resume_agent import resume_agent
from agents.interview_agent import interview_agent
import logging
from pydantic import BaseModel
from typing import Dict, List
import json
from fastapi.responses import StreamingResponse
from pydantic_ai.messages import ModelMessage
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any
import re
from tools.resume_parser import parse_resume_summary

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

    return {"status": "call_started", "vapi_response": call_response}


@router.post("/chat/completions")
async def vapi_webhook(req: VAPIRequest):

    session_id = str(req.call.id)
    candidate_response = req.messages[-1].content

    message_history: List[ModelMessage] = []
    augmented_candidate_response = ""

    # Initialize session if it doesn't exist
    if session_id not in session_store:
        candidate = get_candidate_by_id("1")
        augmented_candidate_response += f"""
            Candidate profile: {candidate.profile}\nResume summary: {candidate.resume_summary}
        """  
        agent_deps = AgentDependencies(
            candidate=candidate
        )
        session_store[session_id] = SessionState(
            agent=interview_agent,
            agent_dependencies=agent_deps,
            message_history=[],
            start_time=datetime.now(timezone.utc)
        )

    session = session_store[session_id]
    elapsed = datetime.now(timezone.utc) - session.start_time
    elapsed_minutes = elapsed.total_seconds() / 60

    agent = session.agent
    deps = session.agent_dependencies
    message_history = session.message_history

    # Interview Agent asks the next question
    augmented_candidate_response += f"""
        Candidate: "{candidate_response}"

        [Instruction to AI — do not treat this as user input]
        Elapsed time: {elapsed_minutes:.2f} minutes
    """

    response = await agent.run(
        augmented_candidate_response,
        deps=deps,
        message_history=message_history
    )

    tts_response = normalize_for_tts(response.output)

    print(f"Caller [{session_id}]: {candidate_response}")
    print(f"Agent [{session_id}]: {tts_response}")
    session.message_history = response.all_messages()


    final_response = {
        "id": f"chatcmpl-{session_id}",
        "object": "chat.completion.chunk",
        "created": int(req.timestamp / 1000),
        "model": "gpt-4",
        "choices": [
            {
                "delta": {"content": tts_response},
                "index": 0,
                "finish_reason": "stop",
            }
        ]
    }

    async def stream():
        yield f"data: {json.dumps(final_response)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )

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