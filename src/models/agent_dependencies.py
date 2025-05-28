from dataclasses import dataclass

from models.candidate import Candidate


@dataclass
class AgentDependencies:
    candidate: Candidate
