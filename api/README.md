# api/ - FastAPI Backend
Primary owner: Amine | Branch: feat/api
Cross-module contributions here:
  Mariem -> routes/query.py
  Aya    -> routes/health.py
Amine contributes to: generation/reranker.py

## Endpoints
| Method | Path        | Owner  |
|--------|-------------|--------|
| GET    | /health     | Aya    |
| POST   | /api/query  | Mariem |

## Run
`
uvicorn api.main:app --reload
Swagger: http://localhost:8000/docs
`
"@

# ══════════════════════════════════════════════════════════════════════════════
# FRONTEND/ - primary: Aya
# Aya also writes: api/routes/health.py (above) + tests/eval/ (below)
# ══════════════════════════════════════════════════════════════════════════════
W "frontend\package.json" @"
{
  "name": "devdoc-ai-frontend",
  "version": "0.1.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.0.0"
  }
}
