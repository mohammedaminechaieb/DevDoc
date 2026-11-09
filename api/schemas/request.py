# api/schemas/request.py
# Primary owner: Amine

from pydantic import BaseModel


class Message(BaseModel):
    role: str      # "user" | "assistant"
    content: str


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    use_graph: bool = True
    history: list[Message] = []   # previous turns, for follow-up questions
