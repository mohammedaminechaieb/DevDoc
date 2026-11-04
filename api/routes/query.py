# api/routes/query.py
# Cross-module owner: Mariem
#
# Mariem writes this because she owns generation and knows the
# exact function signatures that need to be called here.

from fastapi import APIRouter
from api.schemas.request import QueryRequest
from api.schemas.response import QueryResponse

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(body: QueryRequest):
    # TODO: call retrieval.hybrid_retriever.retrieve(body.question, body.top_k)
    # TODO: call generation.answer_generator.generate_answer(...)
    # return QueryResponse(answer=..., sources=..., query=body.question)
    raise NotImplementedError
