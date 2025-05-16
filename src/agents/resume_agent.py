import os
import logfire
from pydantic_ai import Agent, RunContext
from agents.agent_config import RESUME_AGENT_PROMPT, AgentDependencies

from db.candidate_repository import get_candidate_by_id, update_candidate_by_id
from parsers.resume_parser import parse_resume_from_url
from models.candidate import ResumeSummary

# Configure logging
logfire.configure(send_to_logfire='if-token-present')

model = os.getenv("RESUME_LLM_MODEL")
openai_key = os.getenv("OPENAI_API_KEY")
resume_agent = Agent(
    model = model,
    system_prompt = RESUME_AGENT_PROMPT,
    temperature=0.3,
    deps_type=AgentDependencies,
    output_type=str,
    instrument=True
)


@resume_agent.tool
async def fetch_candidate_resume (
    ctx: RunContext[AgentDependencies]
) -> str:
    
    resume_url = ctx.deps.candidate.profile.resume_url
    resume = parse_resume_from_url(resume_url)

    return resume

@resume_agent.tool
async def update_resume_summary_in_db (
    ctx: RunContext[AgentDependencies],
    resume_summary: ResumeSummary
) -> str:

    candidate = ctx.deps.candidate
    candidate.resume_summary = resume_summary

    response = update_candidate_by_id(candidate, ctx.deps.supabase)

    return response