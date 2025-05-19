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
from db.candidate_repository import get_candidate_by_id

# Simulated candidate agent prompt template
CANDIDATE_PROMPT_TEMPLATE = """
You are an AI-powered voice interviewee.

You are playing the role of a software engineer interviewing for a role at Bain & Company.
You must respond in a way that reflects this personality: {personality_description}.
Be consistent in tone and clarity. Your responses should align with your resume summary below.
conversationaly
## Speaking style
- Answer questions conversationally as you are speaking to a real person.
- Don't answer in lenghty format unless your personality suits you.
- Do **not** enumerate ("first," "second," "number three") or show bullets/numbers.
- Avoid written-text cues like "[Pause]."

Your Profile:
{profile}

Resume Summary:
{resume_summary}

Respond with your answer as if you were on a live voice call.
"""

async def simulate_interview(personality: str):

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
        personality_description=personality,
        profile=candidate.profile,
        resume_summary=candidate.resume_summary
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
            print(f"interviewer indicated end {interviewer}")
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

        # Stop if interview agent ends early (e.g., due to Bain prior interview)
        if any(exit_phrase in interviewer.lower() for exit_phrase in ["ending the call"]):
            break

    # Feed the transcript to recommendation agent
    full_transcript = "\n".join([
        f"[{t['role'].capitalize()}: {t['content']}" for t in transcript
    ])

    evaluation_response = await evaluation_agent.run(
        user_prompt=full_transcript,
        deps=agent_deps
        )
    
    print(f"Evaluation results {evaluation_response.output}")

if __name__ == "__main__":
    asyncio.run(simulate_interview("chatty but vague and dodges technical questions"))

#frequently asks follow up questions
#not a strong developer
#chatty but vague and dodges technical questions
#to the point, clear headed, analytical, very strong technical command, hands-on
#casual, inappropriate, figured speaking to AI, foul language
#not interested, harassing interviewer, foul language
#steering outside of interview, hitting on the interviewer