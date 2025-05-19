from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class CandidateProfile(BaseModel):
    candidate_id: str
    name: str
    email: str
    phone: str
    position: Optional[str] = None
    client_name: Optional[str] = None
    resume_file_name: Optional[str] = None
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None

class ResumeSummary(BaseModel):
    experience_summary: Optional[str] = None
    core_technical_skills: List[str] = Field(default_factory=list)
    specialized_technical_skills: List[str] = Field(default_factory=list)
    current_project: Optional[str] = None
    other_notable_projects: List[str] = Field(default_factory=list)
    education_certification: Optional[str] = None
    potential_flags: List[str] = Field(default_factory=list)
    resume_notes: Optional[str] = None

class Scorecard(BaseModel):
    system_design: int = Field(..., ge=1, le=5)
    hands_on_coding: int = Field(..., ge=1, le=5)
    communication: int = Field(..., ge=1, le=5)
    confidence: int = Field(..., ge=1, le=5)
    ownership: int = Field(..., ge=1, le=5)
    problem_solving: int = Field(..., ge=1, le=5)

class CandidateEvaluation(BaseModel):
    scorecard: Scorecard
    interview_transcript: Optional[str] = None
    summary: Optional[str] = None
    recommendation: Optional[Literal["Recommend", "Not Recommend"]] = None

class Candidate(BaseModel):
    profile: CandidateProfile
    resume_summary: Optional[ResumeSummary] = None
    evaluation: Optional[CandidateEvaluation] = None
    status: Optional[str] = None