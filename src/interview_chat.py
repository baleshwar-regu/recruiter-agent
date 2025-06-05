import asyncio
from typing import List

from pydantic_ai.messages import ModelMessage

from agents.interview_agent import interview_agent
from agents.resume_agent import resume_agent
from config import CANDIDATE_ID_TESTING
from db.candidate_repository import get_candidate_by_id
from models.agent_dependencies import AgentDependencies
from tools.resume_parser import parse_resume_summary


async def main():

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

    candidate_exp_summary = f"Candidate profile: {candidate.profile}\nResume summary: {candidate.resume_summary}"

    message_history: List[ModelMessage] = []
    candidate_response = ""

    # Chat loop
    while True:

        if candidate_response.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not message_history:
            candidate_response = candidate_exp_summary

        interview_response = await interview_agent.run(
            user_prompt=candidate_response,
            deps=agent_deps,
            message_history=message_history,
        )

        message_history = interview_response.all_messages()

        print(f"Interviewer: {interview_response.output}")

        # Prompt next input
        candidate_response = input("You: ")


if __name__ == "__main__":
    asyncio.run(main())
