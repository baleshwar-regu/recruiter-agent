from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from models.llm_cost import AgentLLMCost


class CandidateProfile(BaseModel):
    candidate_id: str
    name: str
    email: str
    phone: str
    job_title: Optional[str] = None
    current_employer: Optional[str] = None
    resume_file_name: Optional[str] = None
    resume_url: Optional[str] = None


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
    summary: Optional[str] = None
    recommendation: Optional[Literal["Recommend", "Not Recommend"]] = None


class Cost(BaseModel):
    total_cost: float
    agent_llm_cost: List[str] = Field(default_factory=list)


class Candidate(BaseModel):
    profile: CandidateProfile
    parsed_resume: Optional[str] = None
    resume_summary: Optional[ResumeSummary] = None
    interview_transcript: Optional[str] = None
    evaluation: Optional[CandidateEvaluation] = None
    status: Optional[str] = None
    agent_llm_cost: Optional[AgentLLMCost] = None
    llm_cost: Optional[float] = None
