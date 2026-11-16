# generation/answer_generator.py
# Owner: Ghassen

from generation.llm_client import call_llm
from generation.prompt_builder import SYSTEM_PROMPT, build_prompt
from generation.reranker import rerank

NO_CONTEXT_ANSWER = (
    "I could not find any relevant passage in the documentation to answer this question."
)


def _safe_rerank(query: str, chunks: list[dict]) -> list[dict]:
    """Use Mariem's reranker; fall back to the retriever score while it is not implemented."""
    try:
        return rerank(query, chunks)
    except NotImplementedError:
        # TEMPORARY: remove once generation/reranker.py is merged
        return sorted(chunks, key=lambda c: c.get("score", 0), reverse=True)


def _format_sources(chunks: list[dict]) -> list[dict]:
    """Keep only the fields the API and the frontend need."""
    return [
        {
            "chunk_id": c.get("chunk_id"),
            "url": c.get("url"),
            "framework": c.get("framework"),
            "text": c.get("text"),
        }
        for c in chunks
    ]


def generate_answer(query: str, chunks: list[dict]) -> dict:
    """rerank -> build_prompt -> call_llm.
    Returns: {answer, sources: [{chunk_id, url, framework, text}], query}
    """
    # Nothing retrieved: no need to call the LLM
    if not chunks:
        return {"answer": NO_CONTEXT_ANSWER, "sources": [], "query": query}

    ranked = _safe_rerank(query, chunks)
    prompt = build_prompt(query, ranked)
    answer = call_llm(prompt, system=SYSTEM_PROMPT)

    return {"answer": answer, "sources": _format_sources(ranked), "query": query}