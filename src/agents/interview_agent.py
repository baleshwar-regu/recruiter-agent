import logfire
from pydantic_ai import Agent

from agents.agent_config import INTERVIEW_AGENT_PROMPT
from config import INTERVIEW_LLM_MODEL, OPENAI_KEY
from models.agent_dependencies import AgentDependencies

# Configure logging
logfire.configure(send_to_logfire="if-token-present")

model = INTERVIEW_LLM_MODEL
openai_key = OPENAI_KEY

interview_agent = Agent(
    model=model,
    system_prompt=INTERVIEW_AGENT_PROMPT,
    temperature=0.3,
    deps_type=AgentDependencies,
    output_type=str,
    instrument=True,
)
