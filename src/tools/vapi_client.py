import httpx
import logging
from config import (
    VAPI_API_KEY,
    VAPI_PHONE_NUMBER_ID,
    VAPI_API_BASE_URL,
    VAPI_RECRUITER_ASSISTANT_ID,
    VAPI_INTERVIEW_WEBHOOK_URL,
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
        "Content-Type": "application/json"
    }
    payload = {
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": phone_number   
        },
        "assistantId": VAPI_RECRUITER_ASSISTANT_ID,
        "assistantOverrides": {
            "firstMessage": greeting,
            "model": {
                "provider": "custom-llm",  
                "model": "recruiter-agent",
                "url": VAPI_INTERVIEW_WEBHOOK_URL 
            },
            "metadata": {
                "candidate_id": candidate_id
            }
        }
    }

    logger.info(f"Starting VAPI call to {phone_number} with assistant {VAPI_RECRUITER_ASSISTANT_ID}")

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code not in (200, 201):
        logger.error(f"Failed to start VAPI call: {response.text}")
        response.raise_for_status()
    else:
        logger.info(f"VAPI call started successfully: {response.json().get('id')}")


    return response.json()