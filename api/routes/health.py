# api/routes/health.py
# Cross-module owner: Aya
#
# Aya writes this because the frontend polls /health to check
# if the backend is reachable before enabling the search button.

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok", "service": "devdoc-ai"}
