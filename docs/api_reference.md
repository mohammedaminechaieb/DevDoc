# API Reference

## GET /health
~~~json
{"status": "ok", "service": "agentic-ai-copilot"}
~~~
Polled by the frontend every 20 s.

## POST /api/query
Request:
~~~json
{
  "question": "I want several agents that search the web and write a report. How should I design it?",
  "top_k": 5,
  "use_graph": true,
  "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
}
~~~
- `question`: 3-2000 characters. `top_k`: 1-20 (default 5).
- `use_graph`: true = hybrid retrieval (FAISS + Neo4j fused by RRF), false = vector only.
- `history`: previous turns (the backend reads the last 4) for follow-up questions.

Response `200`:
~~~json
{
  "query": "...",
  "intent": "design",
  "entities": ["Multi-Agent System", "Agent"],
  "answer": "... [1] ... [2]",
  "sources": [{"chunk_id": "...", "url": "...", "framework": "langgraph", "text": "..."}],
  "graph": {"nodes": [{"id": "...", "label": "...", "type": "...", "df": 12, "seed": true}],
            "edges": [{"source": "...", "target": "...", "relation": "USES", "confidence": 0.9,
                       "evidence": "...", "chunk_id": "..."}]},
  "review": {"ok": true, "issues": []}
}
~~~
- `intent`: `learn | recommend | design | code | explore | evaluate` (features A-F of NLP.pdf).
- `sources` are numbered like the `[n]` citations in `answer`.
- `graph`: subgraph of the question's entities, for the GraphViewer (empty when Neo4j is unavailable).
- `review`: deterministic checks (citations, URLs, grounding); `ok=false` lists the issues.

Error codes:
| Code | Meaning |
|---|---|
| 422 | invalid input (empty question, top_k out of range, bad role) |
| 503 | FAISS index not built - run `python -m retrieval.faiss_indexer` |
| 501 | a pipeline stage is not implemented |
| 500 | pipeline error (message in `detail`) |
