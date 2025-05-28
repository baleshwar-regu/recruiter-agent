import logging
from datetime import datetime
from urllib.parse import urlparse

from db.candidate_repository import normalize_phone, upsert_candidate_from_calendly

logger = logging.getLogger(__name__)


def dispatch_event(event_type: str, payload: dict):
    if event_type == "invitee.created":
        return handle_invitee_created(payload)
    elif event_type == "invitee.canceled":
        return handle_invitee_canceled(payload)
    else:
        raise ValueError(f"Unhandled event type: {event_type}")


def extract_candidate_info(payload: dict):
    name = payload.get("name")
    email = payload.get("email")
    phone = ""

    location = payload.get("scheduled_event", {}).get("location", {})
    if location.get("type") == "outbound_call":
        phone = location.get("location")

    return name, email, phone


def handle_invitee_created(payload: dict):
    name, email, raw_phone = extract_candidate_info(payload)

    phone = normalize_phone(raw_phone) if raw_phone else None

    start_time_str = payload.get("scheduled_event", {}).get("start_time")
    if not start_time_str:
        raise ValueError("Missing start_time in Calendly payload")

    scheduled_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))

    logger.info(
        f"upsert_candidate_from_calendly INTERVIEW_SCHEDULED {name} {email} {phone} {scheduled_time}"
    )
    candidate_id = upsert_candidate_from_calendly(
        name=name,
        email=email,
        phone=phone,
        scheduled_time=scheduled_time,
        status="INTERVIEW_SCHEDULED",
    )

    return {
        "status": "scheduled",
        "candidate_id": candidate_id,
        "scheduled_time": scheduled_time.isoformat(),
    }


def handle_invitee_canceled(payload: dict):
    name, email, raw_phone = extract_candidate_info(payload)
    phone = normalize_phone(raw_phone) if raw_phone else None

    logger.info(
        f"upsert_candidate_from_calendly INTERVIEW_CANCELED {name} {email} {phone} scheduled_time None"
    )
    candidate_id = upsert_candidate_from_calendly(
        name=name,
        email=email,
        phone=phone,
        scheduled_time=None,
        status="INTERVIEW_CANCELED",
    )

    return {"status": "cancellation recorded", "candidate_id": candidate_id}


def extract_event_id(url: str) -> str:
    """
    Extract the UUID from a Calendly scheduled_events URL.
    """
    path = urlparse(
        url
    ).path  # => '/scheduled_events/3d5b9b31-f5bd-40a0-95f8-79a423dba88e'
    return path.rstrip("/").split("/")[-1]  # => '3d5b9b31-f5bd-40a0-95f8-79a423dba88e'
