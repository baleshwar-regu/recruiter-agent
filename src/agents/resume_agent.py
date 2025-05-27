import os
import logfire
from pydantic_ai import Agent, RunContext
from agents.agent_config import RESUME_AGENT_PROMPT
from config import RESUME_LLM_MODEL, OPENAI_KEY

from db.candidate_repository import update_candidate_by_id
from models.agent_dependencies import AgentDependencies
from tools.resume_parser import parse_resume_from_url
from models.candidate import ResumeSummary

# Configure logging
logfire.configure(send_to_logfire='if-token-present')

model = RESUME_LLM_MODEL
openai_key = OPENAI_KEY

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
    
    candidate = ctx.deps.candidate
    resume_url = candidate.profile.resume_url
    parsed_resume = parse_resume_from_url(resume_url)
    candidate.parsed_resume = parsed_resume

    return parsed_resume