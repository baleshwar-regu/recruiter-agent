from pydantic_ai.usage import Usage
from tokonomics import calculate_pydantic_cost

from models.llm_cost import LLMCost


async def compute_llm_cost(usage: Usage, model: str) -> LLMCost:

    costs = await calculate_pydantic_cost(model=model, usage=usage)
    if not costs:
        raise ValueError(f"Could not calculate cost for model: {model}")

    return LLMCost(
        prompt_cost=costs.prompt_cost,
        completion_cost=costs.completion_cost,
        total_cost=costs.total_cost,
    )
