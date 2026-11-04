# api/schemas/response.py
# Primary owner: Amine

from pydantic import BaseModel

class Source(BaseModel):
    url: str
    framework: str
    text: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    query: str
