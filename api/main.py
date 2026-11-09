# api/main.py
# Primary owner: Amine
# Run: uvicorn api.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, query

app = FastAPI(
    title="Agentic AI Copilot",
    description="LangGraph multi-agent assistant powered by Hybrid GraphRAG (FAISS + Neo4j)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(query.router, prefix="/api")
