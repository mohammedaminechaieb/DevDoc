# api/routes/health.py
# Owner: Oussema

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "agentic-ai-copilot"}
