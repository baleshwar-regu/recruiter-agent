from datetime import datetime, timezone
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import uuid
from typing import Optional

from models.candidate import Candidate, CandidateProfile, ResumeSummary, Scorecard, CandidateEvaluation

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_candidate_by_id(
        candidate_id: str, 
    ) -> Candidate:

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
        candidate: Candidate
    ) -> str:
    data = {}

    if candidate.parsed_resume:
        data["parsed_resume"] = clean_null_bytes(candidate.parsed_resume)

    if candidate.resume_summary:
        raw_summary = candidate.resume_summary.model_dump(exclude_none=True)
        cleaned_summary = {k: clean_null_bytes(v) for k, v in raw_summary.items()}
        data.update(cleaned_summary)

    if candidate.evaluation:
        data["scorecard"] = candidate.evaluation.scorecard.model_dump()
        data["evaluation_summary"] = candidate.evaluation.summary
        data["recommendation"] = candidate.evaluation.recommendation

    if candidate.interview_transcript:
        data["interview_transcript"] = candidate.interview_transcript

    if candidate.status:
        data["status"] = candidate.status

    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    if not data:
        raise ValueError("No fields to update.")

    response = supabase.table("candidates")\
        .update(data)\
        .eq("candidate_id", candidate.profile.candidate_id)\
        .execute()

    return response

def normalize_phone(phone_str: str, default_country: str = "IN") -> str:
    import phonenumbers
    try:
        parsed = phonenumbers.parse(phone_str, default_country)
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception as e:
        print(f"Phone normalization error: {e}")
        return None

def upsert_candidate_from_calendly(
    name: str,
    email: str,
    phone: str,
    scheduled_time: Optional[datetime],
    status: str = "INTERVIEW_SCHEDULED"
) -> str:
    candidate_id = None

    if phone:
        result = supabase.table("candidates").select("candidate_id").eq("phone", phone).execute()
        if result.data:
            candidate_id = result.data[0]["candidate_id"]

    if not candidate_id and email:
        result = supabase.table("candidates").select("candidate_id").eq("email", email).execute()
        if result.data:
            candidate_id = result.data[0]["candidate_id"]

    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    if scheduled_time:
        data["scheduled_time"] = scheduled_time.isoformat()

    if candidate_id:
        supabase.table("candidates").update(data).eq("candidate_id", candidate_id).execute()
    else:
        candidate_id = str(uuid.uuid4())
        data["candidate_id"] = candidate_id
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        supabase.table("candidates").insert(data).execute()

    return candidate_id

def clean_null_bytes(value):
    if isinstance(value, str):
        return value.replace('\x00', '')
    elif isinstance(value, list):
        return [clean_null_bytes(v) for v in value]
    elif isinstance(value, dict):
        return {k: clean_null_bytes(v) for k, v in value.items()}
    return value