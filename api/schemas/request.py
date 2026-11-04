# api/schemas/request.py
# Primary owner: Amine

from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    use_graph: bool = True
