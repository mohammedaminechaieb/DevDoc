# api/main.py
# Primary owner: Amine
# Run: uvicorn api.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import query, health

app = FastAPI(
    title="DevDoc AI",
    description="Hybrid GraphRAG assistant for technical documentation",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(query.router, prefix="/api")
