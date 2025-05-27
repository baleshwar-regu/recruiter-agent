from models.candidate import Candidate


from dataclasses import dataclass


@dataclass
class AgentDependencies:
    candidate: Candidate