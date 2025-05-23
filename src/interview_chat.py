import asyncio
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from agents.agent_config import AgentDependencies
from agents.resume_agent import resume_agent
from agents.interview_agent import interview_agent
from db.candidate_repository import get_candidate_by_id, update_candidate_by_id
from models.candidate import Candidate, ResumeSummary
from typing import List
from pydantic_ai.messages import ModelMessage
import time
from tools.resume_parser import parse_resume_summary 


async def main():

    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    candidate = get_candidate_by_id(candidate_id="1")

    agent_deps = AgentDependencies(
        candidate=candidate
    )

    message = "analyze the resume for the candidate"
    response = await resume_agent.run(
        message, 
        deps=agent_deps)

    resume_summary = parse_resume_summary(response.output)
    print(f"Resume summary: {resume_summary}")

    candidate.resume_summary = resume_summary
    candidate.status = "RESUME_SUMMARY_GENERATED"

    response = update_candidate_by_id(candidate=candidate)

    start_time = time.time()

    message = f"""
        Candidate profile: {candidate.profile}
        Resume summary: {candidate.resume_summary}
        """
    message_history: List[ModelMessage] = []

    # Chat loop
    while True:

        if message.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        # Later, check elapsed time
        elapsed_minutes = (time.time() - start_time) / 60

        augmented_message = f"""
            [Instruction to AI — do not treat this as user input]
            Elapsed time: {elapsed_minutes:.1f} minutes

            Candidate: "{message}"
            """

        response = await interview_agent.run(
            user_prompt=augmented_message, 
            deps=agent_deps,
            message_history=message_history)
        
        message_history = response.all_messages()
        
        print(f"Interviewer: {response.output}")

        # Prompt next input
        message = input("You: ")

if __name__ == "__main__":
    asyncio.run(main())
