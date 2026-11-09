# api/ - FastAPI Backend
Primary owner: Amine | Branch: feat/api
Cross-module contributions here:
  Mariem -> routes/query.py
  Aya    -> routes/health.py
Amine contributes to: generation/reranker.py

`POST /api/query` calls `agents.orchestrator.run_copilot()` and returns
`501` while parts of the pipeline are still `NotImplementedError`.

## Endpoints
| Method | Path        | Owner  |
|--------|-------------|--------|
| GET    | /health     | Aya    |
| POST   | /api/query  | Mariem |

Full request/response format: [docs/api_reference.md](../docs/api_reference.md)

## Run
```
uvicorn api.main:app --reload
```
Swagger: http://localhost:8000/docs
