from supabase import Client
from datetime import datetime

from models.candidate import Candidate, CandidateProfile, ResumeSummary, Scorecard, CandidateEvaluation


def get_candidate_by_id(
        candidate_id: str, 
        supabase: Client) -> Candidate:
    result = supabase.table("candidates").select("*").eq("candidate_id", candidate_id).single().execute()
    data = result.data

    if not data:
        raise ValueError(f"No candidate found with ID: {candidate_id}")

    profile = CandidateProfile(**{k: data.get(k) for k in CandidateProfile.model_fields.keys()})

    response = supabase.storage.from_("recruiter-agent-resumes").create_signed_url(
        path=profile.resume_file_name,
        expires_in=3600  # valid for 1 hour
        )
    profile.resume_url = response.get("signedUrl") 

    resume_summary = ResumeSummary(
        experience_summary=data.get("experience_summary"),
        core_technical_skills=data.get("core_technical_skills") or [],
        specialized_technical_skills=data.get("specialized_technical_skills") or [],
        current_project=data.get("current_project"),
        other_notable_projects=data.get("other_notable_projects") or [],
        education_certification=data.get("education_certification"),
        potential_flags=data.get("potential_flags") or [],
        resume_notes=data.get("resume_notes")
    ) if data.get("experience_summary") else None

    evaluation = CandidateEvaluation(
        scorecard=Scorecard(**data["scorecard"]),
        summary=data.get("evaluation_summary"),
        recommendation=data.get("recommendation")
    ) if data.get("scorecard") else None

    return Candidate(
        profile=profile,
        resume_summary=resume_summary,
        evaluation=evaluation,
        status=data.get("status")
    )

# update_candidate_by_id
def update_candidate_by_id(
        candidate: Candidate, 
        supabase: Client) -> str:
    data = {}

    # if candidate.profile:
    #     data.update({
    #         k: getattr(candidate.profile, k)
    #         for k in CandidateProfile.model_fields.keys()
    #         if k != "candidate_id" and getattr(candidate.profile, k) is not None
    #     })

    if candidate.resume_summary:
        data.update(candidate.resume_summary.model_dump(exclude_none=True))

    if candidate.evaluation:
        data["scorecard"] = candidate.evaluation.scorecard.model_dump()
        data["evaluation_summary"] = candidate.evaluation.summary
        data["recommendation"] = candidate.evaluation.recommendation

    if candidate.status:
        data["status"] = candidate.status

    data["updated_at"] = datetime.utcnow().isoformat()

    if not data:
        raise ValueError("No fields to update.")

    response = supabase.table("candidates")\
        .update(data)\
        .eq("candidate_id", candidate.profile.candidate_id)\
        .execute()

    return response
