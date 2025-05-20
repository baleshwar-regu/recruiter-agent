import asyncio
import time
from typing import List
from pydantic import Field
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from agents.agent_config import AgentDependencies
from agents.resume_agent import resume_agent
from agents.interview_agent import interview_agent
from agents.evaluation_agent import evaluation_agent
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, INTERVIEW_LLM_MODEL, OPENAI_KEY
from db.candidate_repository import get_candidate_by_id, update_candidate_by_id

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
    openai_key = OPENAI_KEY
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    candidate = get_candidate_by_id(candidate_id="1", supabase=supabase_client)

    agent_deps = AgentDependencies(
        supabase=supabase_client, 
        candidate=candidate)
    
    resume_agent_message = "analyze the resume for the candidate"
    await resume_agent.run(
        resume_agent_message, 
        deps=agent_deps)

    interviewer_message_history: List[ModelMessage] = []
    candidate_message_history: List[ModelMessage] = []
    transcript = []
    interviewer_message = f"Candidate profile: {candidate.profile}\nResume summary: {candidate.resume_summary}"

    # Candidate Agent responds based on personality
    candidate_prompt = CANDIDATE_PROMPT_TEMPLATE.format(
        personality=personality,
        skill=skill
    )

    candidate_agent = Agent(
        model = model,
        system_prompt = candidate_prompt,
        temperature=0.3,
        deps_type=AgentDependencies,
        output_type=str,
        instrument=True
    )

    turn_counter = 0

    def get_elapsed_minutes():
        nonlocal turn_counter       # ← tell Python to bind to the outer turn_counter
        turn_counter += 1
        return turn_counter * 1
 
    # Interview loop
    while True:
        elapsed = get_elapsed_minutes()

        if elapsed > 60:
            break

        # Interview Agent asks the next question
        interviewer_input = f"""
        [Instruction to AI — do not treat this as user input]
        Elapsed time: {elapsed:.1f} minutes

        Candidate: "{interviewer_message}"
        """

        print(f"Elapsed time {elapsed}")

        interviewer_response = await interview_agent.run(
            user_prompt=interviewer_input,
            deps=agent_deps,
            message_history=interviewer_message_history
        )

        interviewer = interviewer_response.output.strip()
        
        if interviewer.find("[END_OF_INTERVIEW_END_CALL]") > 0:
            # await vapi.speak(interviewer.replace("[END_OF_INTERVIEW_END_CALL]", ""), ctx.deps.call_id)
            # end vapi call
            # await vapi.hangup_call(ctx.deps.call_id)
            
            transcript.append({"role": "interviewer", "content": interviewer})
            print(f"Interviewer [END_OF_INTERVIEW_END_CALL]: {interviewer}")
            break

        transcript.append({"role": "interviewer", "content": interviewer})
        interviewer_message_history = interviewer_response.all_messages()

        print(f"Interviewer: {interviewer}")

        candidate_response = await candidate_agent.run(
            user_prompt=interviewer,
            deps=agent_deps,
            message_history=candidate_message_history
            )
        
        candidate_text = candidate_response.output.strip()
        transcript.append({"role": "candidate", "content": candidate_text})
        candidate_message_history = candidate_response.all_messages()
        print(f"Candidate: {candidate_text}")
        
        interviewer_message = candidate_text


    # Feed the transcript to recommendation agent
    full_transcript = "\n".join([
        f"[{t['role'].capitalize()}: {t['content']}" for t in transcript
    ])

    candidate.interview_transcript = full_transcript
    candidate.status = "INTERVIEW_COMPLETE"

    update_candidate_by_id(
        candidate=candidate, 
        supabase=supabase_client)

    evaluation_response = await evaluation_agent.run(
        user_prompt=full_transcript,
        deps=agent_deps
        )

    print(f"Evaluation results {evaluation_response.output}")

if __name__ == "__main__":
    asyncio.run(simulate_interview(
        personality="high in confidence, strong communication",
        skill="very week in .net/c#, weak in concepts and system design, vague technical understanding in architecture"
        ))

# not a strong developer, provides short, weak and wrong answers, very low on confidence
# frequently asks follow up questions
# not a strong developer, wrong answers
# chatty but vague and dodges technical questions
# to the point, clear headed, analytical, very strong technical command, hands-on
# casual, inappropriate, figured speaking to AI, foul language
# not interested, harassing interviewer, foul language
# steering outside of interview, hitting on the interviewer


        # personality="low in confidence, poor communication",
        # skill="no experience with .net/c#/sql, weak in concepts and system design"

        # personality="high in confidence, strong communication",
        # skill="expert in .net/c#/sql, strong in concepts and system design"

        # personality="high in confidence, strong communication",
        # skill="very week in .net/c#, poor in technical Q&A, weak in concepts and system design, vague technical understanding in architecture"