from pydantic import BaseModel
from typing import Optional, Literal, List
from resume_summary import ResumeSummary 
from models.candidate_evaluation import CandidateEvaluation

class CandidateUpdate(BaseModel):
    candidate_id: str
    resume_summary: Optional[ResumeSummary] = None
    interview_transcript: Optional[List[str]] = None
    recommendation: Optional[CandidateEvaluation] = None
    status: Optional[Literal["resume_parsed", "interview_done", "recommendation_complete"]] = None
