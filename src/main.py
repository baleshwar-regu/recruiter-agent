from fastapi import FastAPI
from pydantic import BaseModel
from agents.resume_agent import summarize_resume
from models.candidate_profile import CandidateProfile

import os
from supabase import create_client
from httpx import AsyncClient
from agents.resume_agent import Deps
from supabase import Client


SUPABASE_URL = os.getenv("SUPABASE_API_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")

app = FastAPI()

async def build_deps() -> Deps:
    client = AsyncClient()
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return Deps(client=client, supabase=supabase)

class ResumeRequest(BaseModel):
    candidate_id: str
    name: str
    email: str
    phone: str
    position: str
    client_name: str
    resume_text: str

@app.post("/run-resume/")
async def run_resume(request: ResumeRequest):
    profile = CandidateProfile(**request.dict())
    result = await summarize_resume(profile)
    return {"summary": result.dict()}
