# api/schemas/response.py
# Owner: Amine

from pydantic import BaseModel


class Source(BaseModel):
    chunk_id: str | None = None
    url: str
    framework: str
    text: str


class GraphData(BaseModel):
    nodes: list[dict] = []
    edges: list[dict] = []


class Review(BaseModel):
    ok: bool
    issues: list[str] = []


class QueryResponse(BaseModel):
    query: str
    intent: str | None = None     # learn | recommend | design | code | explore | evaluate
    entities: list[str] = []      # graph entities found in the question
    answer: str
    sources: list[Source]
    graph: GraphData | None = None
    review: Review | None = None