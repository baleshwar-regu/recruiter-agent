from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.interview_routes import router as interview_router
import uvicorn
from config import VAPI_EXPOSE_PORT

app = FastAPI(title="Recruiter Voice Agent")

# Optional CORS setup for local testing or webhooks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route groups
app.include_router(interview_router, prefix="/interview")