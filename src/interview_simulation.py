import asyncio
from typing import List

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from agents.evaluation_agent import evaluation_agent
from agents.interview_agent import interview_agent
from agents.resume_agent import resume_agent
from config import CANDIDATE_ID_TESTING, INTERVIEW_LLM_MODEL
from db.candidate_repository import get_candidate_by_id
from models.agent_dependencies import AgentDependencies
from tools.resume_parser import parse_resume_summary

# Simulated candidate agent prompt template
CANDIDATE_PROMPT_TEMPLATE = """
You are simulating a real candidate in a live voice interview.

Your role: A software engineer interviewing for a .NET / C# / SQL role at Bain & Company.

You must stay completely in character throughout the interview. Respond as if you're a real person — not a bot — and stick to your assigned **personality** and **skill level**:

**Personality:** {personality}  
**Skill level:** {skill}

Speak as if you're on a live phone call with a human interviewer. Respond naturally, even if you're unsure. Ramble, hesitate, over-explain, give sharp answers, or dodge questions — all based on your personality and skill.

You must stay consistent across all responses — if you're vague once, stay vague again. If you're confident once, stay confident throughout. Don't "improve" magically mid-interview.

### Voice & Style
- Stay casual and conversational.
- Do not write — speak. No numbered lists, "first," "second," or written formatting.
- If you're weak at a skill, try to cover it up, change the topic, or give a partial answer.
- If you're strong, answer clearly but not like a Wikipedia page — stay human.

### Memory & Continuity
You are in an ongoing conversation. You've already answered a few questions. Use that context in your responses. Don't repeat what you've said unless asked again.

### Output
Respond ONLY with what you'd say out loud. One spoken voice reply. Nothing else.

"""


async def simulate_interview(personality: str, skill: str):

    model = INTERVIEW_LLM_MODEL

    candidate = get_candidate_by_id(candidate_id=CANDIDATE_ID_TESTING)

    agent_deps = AgentDependencies(candidate=candidate)
    resume_agent_message = "analyze the resume for the candidate"

    resume_agent_response = await resume_agent.run(
        resume_agent_message, deps=agent_deps
    )

    resume_summary = parse_resume_summary(resume_agent_response.output)
    print(f"Resume summary: {resume_summary}")

    candidate.resume_summary = resume_summary
    candidate.status = "RESUME_SUMMARY_GENERATED"

    interviewer_message_history: List[ModelMessage] = []
    candidate_message_history: List[ModelMessage] = []
    transcript = []
    candidate_exp_summary = f"Candidate profile: {candidate.profile}\nResume summary: {candidate.resume_summary}"

    # Candidate Agent responds based on personality
    candidate_prompt = CANDIDATE_PROMPT_TEMPLATE.format(
        personality=personality, skill=skill
    )

    candidate_agent = Agent(
        model=model,
        system_prompt=candidate_prompt,
        temperature=0.3,
        deps_type=AgentDependencies,
        output_type=str,
        instrument=True,
    )

    turn_counter = 0

    def get_elapsed_minutes():
        nonlocal turn_counter
        turn_counter += 1
        return turn_counter * 1

    candidate_response_txt = ""

    # Interview loop
    while True:
        elapsed = get_elapsed_minutes()

        if elapsed > 22:
            break

        if not interviewer_message_history:
            candidate_response_txt = candidate_exp_summary

        transcript.append({"role": "candidate", "content": candidate_response_txt})
        print(f"Candidate: {candidate_response_txt}")

        interviewer_response = await interview_agent.run(
            user_prompt=candidate_response_txt,
            deps=agent_deps,
            message_history=interviewer_message_history,
        )

        interviewer_response_text = interviewer_response.output.strip()
        interviewer_message_history = interviewer_response.all_messages()

        transcript.append({"role": "interviewer", "content": interviewer_response_text})
        print(f"Elapsed time {elapsed} Interviewer: {interviewer_response_text}")

        candidate_response = await candidate_agent.run(
            user_prompt=interviewer_response_text,
            deps=agent_deps,
            message_history=candidate_message_history,
        )

        candidate_response_txt = candidate_response.output.strip()
        candidate_message_history = candidate_response.all_messages()

    # Feed the transcript to recommendation agent
    full_transcript = "\n".join(
        [f"[{t['role'].capitalize()}: {t['content']}" for t in transcript]
    )

    candidate.interview_transcript = full_transcript
    candidate.status = "INTERVIEW_COMPLETE"

    evaluation_response = await evaluation_agent.run(
        user_prompt=full_transcript, deps=agent_deps
    )

    candidate.status = "EVALUATION_GENERATED"

    print(f"Evaluation results {evaluation_response.output}")


if __name__ == "__main__":
    asyncio.run(
        simulate_interview(
            personality="low in confidence, poor communication",
            skill="no experience with .net/c#/sql, weak in concepts and system design",
        )
    )

# personality="low in confidence, poor communication",
# skill="no experience with .net/c#/sql, weak in concepts and system design"

# personality="high in confidence, strong communication",
# skill="expert in .net/c#/sql, strong in concepts and system design"
