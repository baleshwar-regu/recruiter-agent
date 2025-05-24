import requests
import io
import logging
from pdfminer.high_level import extract_text_to_fp
from docx import Document
from urllib.parse import urlparse
import json
from typing import Any
from pydantic import ValidationError
from models.candidate import ResumeSummary
import re

# Suppress noisy PDF parser logs
logging.getLogger("pdfminer").setLevel(logging.ERROR)

def get_file_extension(url: str) -> str:
    path = urlparse(url).path  # safely strip query params
    return path.split('.')[-1].lower()

def parse_resume_from_url(resume_url: str) -> str:
    response = requests.get(resume_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch resume from URL: {resume_url} (status {response.status_code})")

    file_ext = get_file_extension(resume_url)

    if file_ext == "pdf":
        output = io.StringIO()
        with io.BytesIO(response.content) as pdf_stream:
            extract_text_to_fp(pdf_stream, output)
        return output.getvalue()

    elif file_ext == "docx":
        with io.BytesIO(response.content) as docx_stream:
            doc = Document(docx_stream)
            return "\n".join([para.text for para in doc.paragraphs])

    else:
        raise ValueError(f"Unsupported resume format: {file_ext}")

def parse_resume_summary(json_str: str) -> ResumeSummary:
    """
    Given a JSON string from the LLM matching the ResumeSummary schema,
    parse it into a ResumeSummary instance (or raise on validation error).
    """
    try:
        sanitized_json = sanitize_llm_json(json_str)
        payload: Any = json.loads(sanitized_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON returned by LLM: {e}")

    try:
        summary = ResumeSummary(**payload)
    except ValidationError as ve:
        # You can log ve.errors() or ve.json() for debugging
        raise ValueError(f"ResumeSummary validation error: {ve}")

    return summary

def sanitize_llm_json(raw: str) -> str:
    """
    1. Strip Markdown code fences (```json …```)
    2. Extract the first {...} block
    3. Remove any trailing commas before ] or }
    """
    # 1. Remove markdown fences
    raw = re.sub(r"```(?:json)?\s*", "", raw)
    raw = raw.replace("```", "")

    # 2. Extract the first {...} substring
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if match:
        raw = match.group(0)

    # 3. Remove trailing commas:  "item", ]  →  "item" ]
    raw = re.sub(r",\s*(?=[}\]])", "", raw)

    return raw