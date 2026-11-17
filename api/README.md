# api/ - FastAPI Backend
Owner: Amine | Branch: feat/api
Other file here: routes/health.py (Oussema)
Amine also owns: agents/orchestrator.py, agents/state.py, agents/intent_analyzer.py,
config/, Dockerfile, docker-compose.yml

`POST /api/query` calls `agents.orchestrator.run_copilot()`.
Errors: 422 invalid input, 503 FAISS index not built, 501 stage not implemented, 500 pipeline error.

## Endpoints
| Method | Path        | Owner |
|--------|-------------|-------|
| GET    | /health     | Oussema   |
| POST   | /api/query  | Amine |

Full request/response format: [docs/api_reference.md](../docs/api_reference.md)

## Run
~~~
uvicorn api.main:app --reload
~~~
Swagger: http://localhost:8000/docs
