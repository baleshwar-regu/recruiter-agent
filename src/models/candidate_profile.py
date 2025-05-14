# Candidate profile that contains essential metadata and resume text
from pydantic import BaseModel


class CandidateProfile(BaseModel):
    candidate_id: str
    name: str
    email: str
    phone: str
    position: str
    resume_url: str
    resume_text: str  # Raw resume (as a string)