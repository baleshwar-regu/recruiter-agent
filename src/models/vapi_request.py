from typing import List

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class Call(BaseModel):
    id: str
    type: str


class VAPIRequest(BaseModel):
    model: str
    call: Call
    messages: List[Message]
    temperature: float
    max_tokens: int
    metadata: dict
    timestamp: int
    stream: bool
