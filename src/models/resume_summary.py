from pydantic import BaseModel

from typing import Optional
from typing import List


class ResumeSummary(BaseModel):
    experience_summary: str
    core_technical_skills: List[str]
    specialized_technical_skills: List[str]
    current_project: str
    other_notable_projects: List[str]
    education_certification: str
    potential_flags: List[str]
    resume_notes: Optional[str] = None