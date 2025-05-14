import requests
import io
from pdfminer.high_level import extract_text_to_fp
from docx import Document

def parse_resume_from_url(resume_url: str) -> str:
    response = requests.get(resume_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch resume from URL: {resume_url}")

    file_ext = resume_url.split(".")[-1].lower()

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
