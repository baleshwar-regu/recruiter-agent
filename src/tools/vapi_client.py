import logging

import httpx

from config import (
    APPLICATION_BASE_URL,
    VAPI_API_BASE_URL,
    VAPI_API_KEY,
    VAPI_CALL_WEBHOOK_URL,
    VAPI_INTERVIEW_WEBHOOK_URL,
    VAPI_PHONE_NUMBER_ID,
    VAPI_RECRUITER_ASSISTANT_ID,
)

logger = logging.getLogger(__name__)


async def start_vapi_call(
    candidate_id: str,
    phone_number: str,
    greeting: str,
) -> dict:
    """
    Asynchronously initiates a voice call to the given phone number using a VAPI assistant.
    """
    url = f"{VAPI_API_BASE_URL}/call"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {"number": phone_number},
        "assistantId": VAPI_RECRUITER_ASSISTANT_ID,
        "assistantOverrides": {
            "firstMessage": greeting,
            "model": {
                "provider": "custom-llm",
                "model": "recruiter-agent",
                "url": f"{APPLICATION_BASE_URL}/{VAPI_INTERVIEW_WEBHOOK_URL}",
            },
            "server": {
                "timeoutSeconds": 30,
                "url": f"{APPLICATION_BASE_URL}/{VAPI_CALL_WEBHOOK_URL}",
            },
            "metadata": {"candidate_id": candidate_id},
        },
    }

    logger.info(
        f"Starting VAPI call to {phone_number} with assistant {VAPI_RECRUITER_ASSISTANT_ID}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code not in (200, 201):
        logger.error(f"Failed to start VAPI call: {response.text}")
        response.raise_for_status()
    else:
        logger.info(f"VAPI call started successfully: {response.json().get('id')}")

    return response.json()


async def end_vapi_call(call_id: str, control_url: str):
    """
    Ends an active VAPI call by sending the “end-call” control message.
    - call_id: the UUID/SID for the call
    - api_key: if your VAPI endpoint requires auth, pass it here
    """

    url = f"{control_url}/{call_id}/control"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {"type": "end-call"}

    logger.info(
        f"Ending VAPI call {call_id} with assistant {VAPI_RECRUITER_ASSISTANT_ID}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code not in (200, 201):
        logger.error(f"Failed to end VAPI call: {response.text}")
        response.raise_for_status()
    else:
        logger.info(f"VAPI ended successfully: {response.json().get('id')}")


async def get_vapi_call(call_id: str) -> str:
    """
    Fetch the VAPI call by its ID, extract the controlUrl, and
    initialize a SessionState stored in session_store.

    Args:
        call_id: the VAPI call UUID
        api_key: your VAPI Bearer token

    Returns:
        The newly created SessionState for this call_id.
    """
    # 1. Fetch call metadata from VAPI
    url = f"{VAPI_API_BASE_URL}/call/{call_id}"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code not in (200, 201):
        logger.error(f"Failed to fetch VAPI call: {response.text}")
        response.raise_for_status()
    else:
        logger.info(f"VAPI call fetched successfully: {response.json().get('id')}")

    return response.json()
