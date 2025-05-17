import logfire
from pydantic_ai import Agent, RunContext
from config import EVALUATION_LLM_MODEL, OPENAI_KEY
from models.candidate import CandidateEvaluation
from agents.agent_config import EVALUATION_AGENT_PROMPT

model = EVALUATION_LLM_MODEL
openai_key = OPENAI_KEY

evaluation_agent = Agent(
    model=model,
    openai_key=OPENAI_KEY,
    system_prompt=EVALUATION_AGENT_PROMPT,
    output_type=CandidateEvaluation,
    instrument=False
)