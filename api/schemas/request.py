# api/schemas/request.py
# Owner: Amine

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000,
                        examples=["How does tool calling work in LangGraph?"])
    top_k: int = Field(default=5, ge=1, le=20)
    use_graph: bool = True
    history: list[Message] = Field(default_factory=list)   # previous turns, for follow-up questions