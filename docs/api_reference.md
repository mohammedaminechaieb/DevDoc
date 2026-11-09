# API Reference

## GET /health  (owner: Aya)
```json
{"status": "ok", "service": "agentic-ai-copilot"}
```

## POST /api/query  (owner: Mariem)
Request:
```json
{
  "question": "I want several agents that search the web and write a report. How should I design it?",
  "top_k": 5,
  "use_graph": true,
  "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
}
```
Response `200`:
```json
{
  "query": "...",
  "intent": "design",
  "answer": "...",
  "sources": [{"chunk_id": "...", "url": "...", "framework": "langgraph", "text": "..."}],
  "graph": {"nodes": [], "edges": []}
}
```
`intent` is one of `learn, recommend, design, code, explore, evaluate`.
Returns `501` while parts of the pipeline are not implemented yet.
