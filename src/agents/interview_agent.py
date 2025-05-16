import logfire
from pydantic_ai import Agent, RunContext
from config import INTERVIEW_LLM_MODEL, OPENAI_KEY
from agents.agent_config import INTERVIEW_AGENT_PROMPT, AgentDependencies

# Configure logging
logfire.configure(send_to_logfire='if-token-present')

model = INTERVIEW_LLM_MODEL
openai_key = OPENAI_KEY

interview_agent = Agent(
    model = model,
    system_prompt = INTERVIEW_AGENT_PROMPT,
    temperature=0.3,
    deps_type=AgentDependencies,
    output_type=str,
    instrument=True
)


@interview_agent.tool
async def get_candidate_details (
    ctx: RunContext[AgentDependencies]
) -> str:
    
    candidate = ctx.deps.candidate
    return candidate