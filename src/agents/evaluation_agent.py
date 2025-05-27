import logfire
from pydantic_ai import Agent, RunContext
from config import EVALUATION_LLM_MODEL, OPENAI_KEY
from models.agent_dependencies import AgentDependencies
from models.candidate import CandidateEvaluation
from agents.agent_config import EVALUATION_AGENT_PROMPT
from db.candidate_repository import update_candidate_by_id

# Configure logging
logfire.configure(send_to_logfire='if-token-present')

evaluation_agent = Agent(
    model=EVALUATION_LLM_MODEL,
    openai_key=OPENAI_KEY,
    system_prompt=EVALUATION_AGENT_PROMPT,
    output_type=CandidateEvaluation,
    instrument=True
)

@evaluation_agent.tool
async def update_candidate_evaluation_in_db (
    ctx: RunContext[AgentDependencies],
    candidate_evaluation: CandidateEvaluation
) -> str:

    candidate = ctx.deps.candidate

    candidate.evaluation = candidate_evaluation
    candidate.status = "EVALUATION_GENERATED"

    response = update_candidate_by_id(candidate=candidate)

    return response