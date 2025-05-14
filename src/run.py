import asyncio
from httpx import AsyncClient
from .agents.resume_agent import summarize_resume
from .models import CandidateProfile

async def main():
    profile = CandidateProfile(
        candidate_id="123",
        name="John Doe",
        email="john@example.com",
        phone="+1234567890",
        position="Software Engineer",
        client_name="Client ABC",
        resume_text="Experienced Python developer with a focus on backend development."
    )
    
    result = await summarize_resume(profile)

if __name__ == "__main__":
    asyncio.run(main())
