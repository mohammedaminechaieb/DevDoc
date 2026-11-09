# api/ - FastAPI Backend
Owner: Amine | Branch: feat/api
Other file here: routes/health.py (Aya)
Amine also owns: agents/orchestrator.py, agents/state.py, agents/intent_analyzer.py,
config/, Dockerfile, docker-compose.yml

`POST /api/query` calls `agents.orchestrator.run_copilot()` and returns
`501` while parts of the pipeline are still `NotImplementedError`.

## Endpoints
| Method | Path        | Owner |
|--------|-------------|-------|
| GET    | /health     | Aya   |
| POST   | /api/query  | Amine |

Full request/response format: [docs/api_reference.md](../docs/api_reference.md)

## Run
~~~
uvicorn api.main:app --reload
~~~
Swagger: http://localhost:8000/docs
