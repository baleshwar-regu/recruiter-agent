from pydantic import BaseModel, Field
from typing import Literal

class Scorecard(BaseModel):
    system_design: int = Field(..., ge=1, le=5)
    hands_on_coding: int = Field(..., ge=1, le=5)
    communication: int = Field(..., ge=1, le=5)
    confidence: int = Field(..., ge=1, le=5)
    ownership: int = Field(..., ge=1, le=5)
    problem_solving: int = Field(..., ge=1, le=5)

class CandidateEvaluation(BaseModel):
    scorecard: Scorecard
    summary: str = Field(..., description="5-8 sentence summary of the candidate's performance")
    recommendation: Literal["Recommend", "Not Recommend"]
