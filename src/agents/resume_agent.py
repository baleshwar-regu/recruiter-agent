import os
import logfire
from pydantic_ai import Agent, RunContext
from agent_config import RESUME_AGENT_PROMPT, AgentDependencies

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
    ctx: RunContext[AgentDependencies],
    candidate_id: str
) -> list[str]:
    
    return []