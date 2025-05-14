from supabase import Client
from typing import Optional

from models.candidate_profile import CandidateProfile
from models.resume_summary import ResumeSummary
from models.candidate_evaluation import Scorecard, CandidateEvaluation


def get_candidate_by_id(candidate_id: str, supabase_client: Client):
    result = supabase_client.table("CandidateProfile")\
        .select("*")\
        .eq("candidate_id", candidate_id)\
        .single()\
        .execute()
    
    data = result.data

    if not data:
        raise ValueError(f"No candidate found with ID: {candidate_id}")

    profile = CandidateProfile(**{
        k: data[k] for k in CandidateProfile.model_fields.keys()
    })

    resume_summary = ResumeSummary(
        experience_summary=data["experience_summary"],
        core_technical_skills=data["core_technical_skills"],
        specialized_technical_skills=data["specialized_technical_skills"],
        current_project=data["current_project"],
        other_notable_projects=data["other_notable_projects"],
        education_certification=data["education_certification"],
        potential_flags=data["potential_flags"],
        resume_notes=data.get("resume_notes")
    )

    scorecard_data = data.get("scorecard")
    evaluation = CandidateEvaluation(
        scorecard=Scorecard(**scorecard_data),
        summary=data.get("evaluation_summary", ""),
        recommendation=data.get("recommendation", "Not Recommend")
    )

    return profile, resume_summary, evaluation

def update_candidate_by_id(
    candidate_id: str,
    supabase_client: Client,
    profile: Optional[CandidateProfile] = None,
    resume_summary: Optional[ResumeSummary] = None,
    evaluation: Optional[CandidateEvaluation] = None,
    status: Optional[str] = None
):
    update_fields = {}

    # Flatten CandidateProfile
    if profile:
        update_fields.update({
            k: getattr(profile, k)
            for k in CandidateProfile.model_fields.keys()
            if getattr(profile, k) is not None and k != "candidate_id"
        })

    # Flatten ResumeSummary
    if resume_summary:
        update_fields.update(resume_summary.model_dump(exclude_none=True))

    # Flatten Evaluation
    if evaluation:
        update_fields["scorecard"] = evaluation.scorecard.model_dump()
        update_fields["evaluation_summary"] = evaluation.summary
        update_fields["recommendation"] = evaluation.recommendation

    # Optional status override
    if status:
        update_fields["status"] = status

    if not update_fields:
        raise ValueError("No fields provided to update.")

    result = supabase_client.table("CandidateProfile")\
        .update(update_fields)\
        .eq("candidate_id", candidate_id)\
        .execute()