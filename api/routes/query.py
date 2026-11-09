# api/routes/query.py
# Owner: Amine

from fastapi import APIRouter, HTTPException

from agents.orchestrator import run_copilot
from api.schemas.request import QueryRequest
from api.schemas.response import QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_endpoint(body: QueryRequest):
    try:
        result = run_copilot(
            body.question,
            top_k=body.top_k,
            use_graph=body.use_graph,
            history=[m.model_dump() for m in body.history],
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=f"Pipeline not implemented yet: {e}")
    return QueryResponse(
        query=body.question,
        intent=result.get("intent"),
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        graph=result.get("graph"),
    )
