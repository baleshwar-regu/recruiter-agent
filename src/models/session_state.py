from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import Usage

from models.agent_dependencies import AgentDependencies


@dataclass
class SessionState:
    agent: Any
    agent_dependencies: AgentDependencies
    resume_agent_usage: Usage
    interview_agent_usage: Usage
    evaluation_agent_usage: Usage
    message_history: List[ModelMessage]
    start_time: datetime
    control_url: str
    transcript: List[Dict[str, str]] = field(default_factory=list)
    end_call: bool = False


# Session store for multiple callers
session_store: dict[str, SessionState] = {}
