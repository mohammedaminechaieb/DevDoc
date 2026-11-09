# frontend/ - React UI
Primary owner: Aya | Branch: feat/frontend
Aya also contributes to: api/routes/health.py + tests/eval/

## Features
- Question box sends `{question, top_k, use_graph, history}` to `POST /api/query`
- Shows the detected mode (intent), the answer, the sources and the knowledge-graph view
- Keeps the conversation history so follow-up questions work

## Mock mode
Home.jsx falls back to a hardcoded mock when the backend is offline,
so the UI can be developed independently.

## Run
```
cd frontend
npm install
npm run dev
```
App: http://localhost:5173 (proxies `/api` and `/health` to http://localhost:8000)
