import os

# Third-party library imports
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

RESUME_LLM_MODEL = os.getenv("RESUME_LLM_MODEL")
INTERVIEW_LLM_MODEL = os.getenv("INTERVIEW_LLM_MODEL")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
