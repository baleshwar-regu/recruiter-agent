import requests
import io
import logging
from pdfminer.high_level import extract_text_to_fp
from docx import Document
from urllib.parse import urlparse

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