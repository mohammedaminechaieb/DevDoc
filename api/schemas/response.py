# api/schemas/response.py
# Primary owner: Amine

from pydantic import BaseModel


class Source(BaseModel):
    chunk_id: str | None = None
    url: str
    framework: str
    text: str


class GraphData(BaseModel):
    nodes: list[dict] = []
    edges: list[dict] = []


class QueryResponse(BaseModel):
    query: str
    intent: str | None = None     # learn | recommend | design | code | explore | evaluate
    answer: str
    sources: list[Source]
    graph: GraphData | None = None
