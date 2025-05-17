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


# @interview_agent.tool
# async def end_interview (
#     ctx: RunContext[AgentDependencies]
# ) -> str:
    
#     candidate_name = ctx.deps.candidate.profile.name
#     #TODO call vapi to end call
#     end_message = f"Let's end the call here. {candidate_name}, it was my pleasure speaking with you. I will pass on my feedback to HR for the next steps."
#     return {"action": "end_interview", "message": end_message}