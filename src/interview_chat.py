import asyncio
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from agents.agent_config import AgentDependencies
from agents.resume_agent import resume_agent
from agents.interview_agent import interview_agent
from db.candidate_repository import get_candidate_by_id
from models.candidate import Candidate
from typing import List
from pydantic_ai.messages import ModelMessage
import time


async def main():

    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    candidate = get_candidate_by_id(candidate_id="1", supabase=supabase_client)

    agent_deps = AgentDependencies(
        supabase=supabase_client,
        candidate=candidate
    )

    message = "analyze the resume for the candidate"
    response = await resume_agent.run(
        message, 
        deps=agent_deps)

    print(f"Resume summary: {response.output}")

    candidate = get_candidate_by_id(candidate_id="1", supabase=supabase_client)

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
