from typing import Optional

from pydantic import BaseModel


class LLMCost(BaseModel):
    prompt_cost: float
    completion_cost: float
    total_cost: float


class AgentLLMCost(BaseModel):
    resume_agent: Optional[LLMCost] = None
    interview_agent: Optional[LLMCost] = None
    evaluation_agent: Optional[LLMCost] = None

    def total_llm_cost(self) -> float:
        total = 0.0
        if self.resume_agent:
            total += self.resume_agent.total_cost
        if self.interview_agent:
            total += self.interview_agent.total_cost
        if self.evaluation_agent:
            total += self.evaluation_agent.total_cost
        return round(total, 6)
