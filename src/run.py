import asyncio
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from agents.agent_config import AgentDependencies
from agents.resume_agent import resume_agent
from db.candidate_repository import get_candidate_by_id
from models.candidate import Candidate





agent = resume_agent
message = "analyze the resume for candidate_id 1"

async def main():

    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    candidate = get_candidate_by_id(candidate_id="1", supabase=supabase_client)

    agent_deps = AgentDependencies(
        supabase=supabase_client,
        candidate=candidate
    )

    response = await agent.run(
        message, 
        deps=agent_deps)

    print(f"Resume summary: {response.output}")

if __name__ == "__main__":
    asyncio.run(main())
