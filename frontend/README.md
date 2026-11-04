# frontend/ - React UI
Primary owner: Aya | Branch: feat/frontend
Aya also contributes to: api/routes/health.py + tests/eval/

## Mock mode
Home.jsx falls back to hardcoded mock when backend is offline,
so Aya can develop the UI independently.

## Run
`
cd frontend && npm install && npm run dev
App: http://localhost:5173
`
"@

# ══════════════════════════════════════════════════════════════════════════════
# TESTS - each person owns one unit test file
# eval/ written by Aya (cross-module: she runs the full pipeline)
# ══════════════════════════════════════════════════════════════════════════════
W "tests\__init__.py" ""

W "tests\unit\test_extractor.py" @"
# tests/unit/test_extractor.py - Owner: Oussema
import pytest
from graph.entity_extractor import extract_entities

CHUNK = {
    "chunk_id": "lc_001",
    "text": "FastAPI uses Pydantic for data validation.",
    "framework": "fastapi",
    "url": "https://fastapi.tiangolo.com/"
}

def test_returns_list():
    assert isinstance(extract_entities(CHUNK), list)

def test_finds_fastapi():
    names = [e["name"] for e in extract_entities(CHUNK)]
    assert "FastAPI" in names
