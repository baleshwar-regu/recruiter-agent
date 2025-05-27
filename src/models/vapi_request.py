

from pydantic import BaseModel


from typing import List


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