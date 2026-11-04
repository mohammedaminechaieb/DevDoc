Set-Location "C:\Users\moham\Documents\PROJECTS\nlp"

# ── GIT INIT ──────────────────────────────────────────────────────────────────
git init
git branch -M main

# ── FOLDERS ───────────────────────────────────────────────────────────────────
$dirs = @(
    "data","config",
    "graph","retrieval","generation",
    "api\routes","api\schemas",
    "frontend\src\components","frontend\src\pages",
    "tests\unit","tests\integration","tests\eval",
    "notebooks","docs","scripts"
)
foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

# ── CORPUS ────────────────────────────────────────────────────────────────────
if (Test-Path "full_corpus\full_corpus_clean.jsonl") {
    Copy-Item "full_corpus\full_corpus_clean.jsonl" "data\full_corpus_clean.jsonl"
}

function W($path, $content) { $content | Out-File -Encoding utf8 $path }

# ══════════════════════════════════════════════════════════════════════════════
# ROOT FILES
# ══════════════════════════════════════════════════════════════════════════════
W ".gitignore" @"
__pycache__/
*.py[cod]
.env
venv/
.venv/
data/full_corpus_clean.jsonl
*.jsonl
*.index
*.faiss
neo4j_data/
frontend/node_modules/
frontend/dist/
.DS_Store
Thumbs.db
"@

W "requirements.txt" @"
faiss-cpu
sentence-transformers
neo4j
spacy
groq
fastapi
uvicorn[standard]
pydantic
jsonlines
tqdm
pytest
python-dotenv
"@

W "pyproject.toml" @"
[project]
name = "devdoc-ai"
version = "0.1.0"
description = "Hybrid GraphRAG assistant for technical documentation"
requires-python = ">=3.10"
"@

W "docker-compose.yml" @"
version: "3.9"
services:
  neo4j:
    image: neo4j:5.18
    ports: ["7474:7474","7687:7687"]
    environment:
      NEO4J_AUTH: neo4j/password
    volumes: [neo4j_data:/data]
  api:
    build: .
    ports: ["8000:8000"]
    depends_on: [neo4j]
    env_file: config/.env.example
volumes:
  neo4j_data:
"@

W "README.md" @"
# DevDoc AI - Hybrid GraphRAG for Technical Documentation

Answers questions about technical frameworks (LangGraph, LangChain,
CrewAI, AutoGen, MCP, OpenAI, Anthropic) using FAISS + Neo4j.

## Team and ownership
| Person  | Primary module | Also contributes to                     |
|---------|----------------|-----------------------------------------|
| Oussema | graph/         | retrieval/graph_retriever.py            |
| Ghassen | retrieval/     | graph/queries.py                        |
| Mariem  | generation/    | api/routes/query.py                     |
| Amine   | api/           | generation/reranker.py                  |
| Aya     | frontend/      | api/routes/health.py + tests/eval/      |

## Quick start
See docs/setup.md
"@

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
W "config\settings.py" @"
# config/settings.py - Shared by all modules
from dotenv import load_dotenv
import os

load_dotenv()

CORPUS_PATH  = os.getenv("CORPUS_PATH",  "data/full_corpus_clean.jsonl")
NEO4J_URI    = os.getenv("NEO4J_URI",    "bolt://localhost:7687")
NEO4J_USER   = os.getenv("NEO4J_USER",   "neo4j")
NEO4J_PASS   = os.getenv("NEO4J_PASS",   "password")
FAISS_INDEX  = os.getenv("FAISS_INDEX",  "data/faiss.index")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL    = os.getenv("LLM_MODEL",    "llama3-8b-8192")
EMBED_MODEL  = os.getenv("EMBED_MODEL",  "sentence-transformers/all-MiniLM-L6-v2")
TOP_K        = int(os.getenv("TOP_K",    "5"))
"@

W "config\.env.example" @"
CORPUS_PATH=data/full_corpus_clean.jsonl
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=password
FAISS_INDEX=data/faiss.index
LLM_PROVIDER=groq
LLM_MODEL=llama3-8b-8192
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
GROQ_API_KEY=your_key_here
TOP_K=5
"@

# ══════════════════════════════════════════════════════════════════════════════
# GRAPH/ - primary: Oussema
# graph/queries.py written by Ghassen (cross-module)
# retrieval/graph_retriever.py written by Oussema (cross-module, see retrieval/)
# ══════════════════════════════════════════════════════════════════════════════
W "graph\__init__.py" "# graph/__init__.py"

W "graph\schema.py" @"
# graph/schema.py
# Primary owner: Oussema

NODE_LABELS = [
    "Technology","Library","Class","Function",
    "Method","Concept","Parameter","DocSection"
]

RELATION_TYPES = [
    "USES","DEFINES","EXTENDS","ACCEPTS",
    "DOCUMENTED_IN","DEPENDS_ON","PROVIDES","RETURNS"
]
"@

W "graph\entity_extractor.py" @"
# graph/entity_extractor.py
# Primary owner: Oussema
#
# Input:  one chunk dict {chunk_id, text, framework, url, ...}
# Output: list[{name, type, chunk_id}]

import spacy
nlp = spacy.load("en_core_web_sm")

TECH_KEYWORDS = [
    "FastAPI","Pydantic","LangChain","LangGraph",
    "CrewAI","AutoGen","MCP","FAISS","Neo4j","React","Docker"
]

def extract_entities(chunk: dict) -> list[dict]:
    # TODO: NER + keyword matching on chunk["text"]
    raise NotImplementedError
"@

W "graph\relation_extractor.py" @"
# graph/relation_extractor.py
# Primary owner: Oussema
#
# Input:  chunk dict + entities list from extract_entities()
# Output: list[{source, target, relation, chunk_id}]

def extract_relations(chunk: dict, entities: list[dict]) -> list[dict]:
    # TODO: rule-based + LLM relation extraction
    raise NotImplementedError
"@

W "graph\neo4j_loader.py" @"
# graph/neo4j_loader.py
# Primary owner: Oussema
#
# Reads data/full_corpus_clean.jsonl -> extracts -> loads into Neo4j

from neo4j import GraphDatabase
from config.settings import NEO4J_URI, NEO4J_USER, NEO4J_PASS, CORPUS_PATH
from graph.entity_extractor import extract_entities
from graph.relation_extractor import extract_relations

def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def load_entities(driver, entities: list[dict]):
    # TODO: MERGE nodes into Neo4j
    raise NotImplementedError

def load_relations(driver, relations: list[dict]):
    # TODO: MERGE relationships into Neo4j
    raise NotImplementedError

if __name__ == "__main__":
    import jsonlines
    driver = get_driver()
    with jsonlines.open(CORPUS_PATH) as reader:
        for chunk in reader:
            ents = extract_entities(chunk)
            rels = extract_relations(chunk, ents)
            load_entities(driver, ents)
            load_relations(driver, rels)
    driver.close()
    print("Graph loaded.")
"@

# graph/queries.py - written by Ghassen (cross-module contribution)
W "graph\queries.py" @"
# graph/queries.py
# Cross-module owner: Ghassen
#
# Ghassen writes this because he uses these helpers directly
# in retrieval/graph_retriever.py that he also owns indirectly.

def query_related_entities(driver, entity_name: str, depth: int = 2) -> list[dict]:
    # TODO: return nodes related to entity_name up to `depth` hops
    raise NotImplementedError

def query_entity_chunks(driver, entity_name: str) -> list[str]:
    # TODO: return chunk_ids that mention this entity
    raise NotImplementedError
"@

W "graph\README.md" @"
# graph/ - Knowledge Graph
Primary owner: Oussema | Branch: feat/graph
Cross-module contribution here: Ghassen (queries.py)

## Pipeline
1. Load data/full_corpus_clean.jsonl
2. entity_extractor.py - NER per chunk
3. relation_extractor.py - relations between entities
4. neo4j_loader.py - push to Neo4j
5. queries.py (Ghassen) - Cypher helpers used by retrieval

## Run
```
docker compose up neo4j -d
python -m graph.neo4j_loader
```
"@

# ══════════════════════════════════════════════════════════════════════════════
# RETRIEVAL/ - primary: Ghassen
# retrieval/graph_retriever.py written by Oussema (cross-module)
# graph/queries.py written by Ghassen (see graph/ above)
# ══════════════════════════════════════════════════════════════════════════════
W "retrieval\__init__.py" "# retrieval/__init__.py"

W "retrieval\embedder.py" @"
# retrieval/embedder.py
# Primary owner: Ghassen

from sentence_transformers import SentenceTransformer
from config.settings import EMBED_MODEL

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model

def embed(texts: list[str]):
    # TODO: return np.ndarray of shape (len(texts), 384)
    raise NotImplementedError
"@

W "retrieval\faiss_indexer.py" @"
# retrieval/faiss_indexer.py
# Primary owner: Ghassen
#
# Reads data/full_corpus_clean.jsonl, embeds every chunk,
# builds FAISS IndexFlatL2, saves to FAISS_INDEX path.

import faiss
from config.settings import CORPUS_PATH, FAISS_INDEX

def build_index():
    # TODO: load corpus, embed chunks, build index, save
    raise NotImplementedError

def load_index() -> faiss.Index:
    # TODO: load from FAISS_INDEX path
    raise NotImplementedError

if __name__ == "__main__":
    build_index()
    print("FAISS index built.")
"@

W "retrieval\faiss_retriever.py" @"
# retrieval/faiss_retriever.py
# Primary owner: Ghassen

from retrieval.embedder import embed
from retrieval.faiss_indexer import load_index

def retrieve_vector(query: str, k: int = 5) -> list[dict]:
    # TODO: embed query, search FAISS, map indices back to chunks
    raise NotImplementedError
"@

# retrieval/graph_retriever.py - written by Oussema (cross-module contribution)
W "retrieval\graph_retriever.py" @"
# retrieval/graph_retriever.py
# Cross-module owner: Oussema
#
# Oussema writes this because he built the graph and knows
# exactly which Cypher patterns to use here.

from graph.queries import query_related_entities, query_entity_chunks

def retrieve_graph(query: str, k: int = 5) -> list[dict]:
    # TODO: extract entities from query, traverse graph, return related chunks
    raise NotImplementedError
"@

W "retrieval\hybrid_retriever.py" @"
# retrieval/hybrid_retriever.py
# Primary owner: Ghassen
#
# Merges FAISS and Neo4j results, deduplicates by chunk_id.

from retrieval.faiss_retriever import retrieve_vector
from retrieval.graph_retriever import retrieve_graph

def retrieve(query: str, k: int = 5) -> list[dict]:
    # TODO: combine both result sets, deduplicate by chunk_id, return top-k
    raise NotImplementedError
"@

W "retrieval\README.md" @"
# retrieval/ - Hybrid Retrieval
Primary owner: Ghassen | Branch: feat/retrieval
Cross-module contribution here: Oussema (graph_retriever.py)
Ghassen contributes to: graph/queries.py

## Pipeline
1. embedder.py - sentence-transformers
2. faiss_indexer.py - build + save FAISS index (run once)
3. faiss_retriever.py - vector search
4. graph_retriever.py (Oussema) - Neo4j traversal
5. hybrid_retriever.py - merge + deduplicate

## Run
```
python -m retrieval.faiss_indexer
```
"@

# ══════════════════════════════════════════════════════════════════════════════
# GENERATION/ - primary: Mariem
# generation/reranker.py written by Amine (cross-module)
# api/routes/query.py written by Mariem (cross-module, see api/)
# ══════════════════════════════════════════════════════════════════════════════
W "generation\__init__.py" "# generation/__init__.py"

# generation/reranker.py - written by Amine (cross-module contribution)
W "generation\reranker.py" @"
# generation/reranker.py
# Cross-module owner: Amine
#
# Amine writes this because he owns the API and needs to know
# exactly what score fields come out before wiring the route.

def rerank(query: str, chunks: list[dict]) -> list[dict]:
    # TODO: score each chunk against query (cross-encoder or BM25 fallback)
    # Returns chunks sorted by relevance score descending
    raise NotImplementedError
"@

W "generation\prompt_builder.py" @"
# generation/prompt_builder.py
# Primary owner: Mariem

SYSTEM_PROMPT = (
    "You are DevDoc AI, an expert assistant for technical documentation. "
    "Answer ONLY from the provided context. "
    "If the answer is not in the context, say so explicitly. "
    "Always cite the source URL and framework."
)

def build_prompt(query: str, chunks: list[dict]) -> str:
    # TODO: format chunks as numbered context blocks, append question
    raise NotImplementedError
"@

W "generation\llm_client.py" @"
# generation/llm_client.py
# Primary owner: Mariem

from config.settings import LLM_PROVIDER, LLM_MODEL

def call_llm(prompt: str) -> str:
    if LLM_PROVIDER == "groq":
        # TODO: call Groq API, return response text
        raise NotImplementedError
    elif LLM_PROVIDER == "ollama":
        # TODO: call local Ollama endpoint
        raise NotImplementedError
    raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")
"@

W "generation\answer_generator.py" @"
# generation/answer_generator.py
# Primary owner: Mariem

from generation.reranker import rerank
from generation.prompt_builder import build_prompt
from generation.llm_client import call_llm

def generate_answer(query: str, chunks: list[dict]) -> dict:
    # TODO: rerank -> build_prompt -> call_llm
    # Returns: {answer, sources: [{url, framework, text}], query}
    raise NotImplementedError
"@

W "generation\README.md" @"
# generation/ - Answer Generation
Primary owner: Mariem | Branch: feat/generation
Cross-module contribution here: Amine (reranker.py)
Mariem contributes to: api/routes/query.py

## Pipeline
1. reranker.py (Amine) - re-score chunks
2. prompt_builder.py - format context + question
3. llm_client.py - Groq / Ollama
4. answer_generator.py - orchestrates all three

## Output
{answer: str, sources: [{url, framework, text}], query: str}
"@

# ══════════════════════════════════════════════════════════════════════════════
# API/ - primary: Amine
# api/routes/query.py written by Mariem (cross-module)
# api/routes/health.py written by Aya (cross-module)
# Amine contributes to: generation/reranker.py (see generation/ above)
# ══════════════════════════════════════════════════════════════════════════════
W "api\__init__.py" "# api/__init__.py"
W "api\routes\__init__.py" "# api/routes/__init__.py"
W "api\schemas\__init__.py" "# api/schemas/__init__.py"

W "api\main.py" @"
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
"@

W "api\schemas\request.py" @"
# api/schemas/request.py
# Primary owner: Amine

from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    use_graph: bool = True
"@

W "api\schemas\response.py" @"
# api/schemas/response.py
# Primary owner: Amine

from pydantic import BaseModel

class Source(BaseModel):
    url: str
    framework: str
    text: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    query: str
"@

# api/routes/query.py - written by Mariem (cross-module contribution)
W "api\routes\query.py" @"
# api/routes/query.py
# Cross-module owner: Mariem
#
# Mariem writes this because she owns generation and knows the
# exact function signatures that need to be called here.

from fastapi import APIRouter
from api.schemas.request import QueryRequest
from api.schemas.response import QueryResponse

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(body: QueryRequest):
    # TODO: call retrieval.hybrid_retriever.retrieve(body.question, body.top_k)
    # TODO: call generation.answer_generator.generate_answer(...)
    # return QueryResponse(answer=..., sources=..., query=body.question)
    raise NotImplementedError
"@

# api/routes/health.py - written by Aya (cross-module contribution)
W "api\routes\health.py" @"
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
"@

W "api\README.md" @"
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
```
uvicorn api.main:app --reload
Swagger: http://localhost:8000/docs
```
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
"@

W "frontend\vite.config.js" @"
// frontend/vite.config.js - Aya
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://localhost:8000' }
  }
})
"@

W "frontend\index.html" @"
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DevDoc AI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"@

W "frontend\src\main.jsx" @"
// frontend/src/main.jsx - Aya
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
)
"@

W "frontend\src\App.jsx" @"
// frontend/src/App.jsx - Aya
import React from 'react'
import Home from './pages/Home'

export default function App() {
  return <Home />
}
"@

W "frontend\src\pages\Home.jsx" @"
// frontend/src/pages/Home.jsx - Aya
import React, { useState } from 'react'
import SearchBar from '../components/SearchBar'
import AnswerCard from '../components/AnswerCard'
import SourcesList from '../components/SourcesList'
import axios from 'axios'

// Mock response - use this while backend is not ready
const MOCK = {
  answer: "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
  sources: [{ url: "https://docs.langchain.com/langgraph/overview", framework: "langgraph", text: "..." }],
  query: "What is LangGraph?"
}

export default function Home() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [healthy, setHealthy] = useState(null)

  // Poll /health before enabling search (Aya owns /health too)
  React.useEffect(() => {
    axios.get('/health')
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false))
  }, [])

  async function handleSearch(question) {
    setLoading(true)
    try {
      const res = await axios.post('/api/query', { question, top_k: 5, use_graph: true })
      setResult(res.data)
    } catch {
      // Fall back to mock while backend is under development
      setResult({ ...MOCK, query: question })
    }
    setLoading(false)
  }

  return (
    <div>
      <h1>DevDoc AI</h1>
      {healthy === false && <p style={{color:'red'}}>Backend offline - using mock data</p>}
      <SearchBar onSearch={handleSearch} disabled={loading} />
      {loading && <p>Loading...</p>}
      {result && <AnswerCard answer={result.answer} />}
      {result && <SourcesList sources={result.sources} />}
    </div>
  )
}
"@

W "frontend\src\components\SearchBar.jsx" @"
// frontend/src/components/SearchBar.jsx - Aya
import React, { useState } from 'react'

export default function SearchBar({ onSearch, disabled }) {
  const [input, setInput] = useState('')
  return (
    <div>
      <input
        type="text"
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && !disabled && onSearch(input)}
        placeholder="Ask about LangGraph, CrewAI, MCP..."
      />
      <button onClick={() => onSearch(input)} disabled={disabled}>Search</button>
    </div>
  )
}
"@

W "frontend\src\components\AnswerCard.jsx" @"
// frontend/src/components/AnswerCard.jsx - Aya
import React from 'react'

export default function AnswerCard({ answer }) {
  return (
    <div>
      <h3>Answer</h3>
      <p>{answer}</p>
    </div>
  )
}
"@

W "frontend\src\components\SourcesList.jsx" @"
// frontend/src/components/SourcesList.jsx - Aya
import React from 'react'

export default function SourcesList({ sources }) {
  return (
    <div>
      <h3>Sources</h3>
      <ul>
        {sources.map((s, i) => (
          <li key={i}>
            <a href={s.url} target="_blank" rel="noreferrer">[{s.framework}] {s.url}</a>
          </li>
        ))}
      </ul>
    </div>
  )
}
"@

W "frontend\src\components\GraphViewer.jsx" @"
// frontend/src/components/GraphViewer.jsx - Aya
// TODO: integrate Neo4j Bloom or react-force-graph
import React from 'react'

export default function GraphViewer({ data }) {
  return (
    <div>
      <h3>Knowledge Graph</h3>
      <p>Graph visualization - coming soon.</p>
    </div>
  )
}
"@

W "frontend\README.md" @"
# frontend/ - React UI
Primary owner: Aya | Branch: feat/frontend
Aya also contributes to: api/routes/health.py + tests/eval/

## Mock mode
Home.jsx falls back to hardcoded mock when backend is offline,
so Aya can develop the UI independently.

## Run
```
cd frontend && npm install && npm run dev
App: http://localhost:5173
```
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
"@

W "tests\unit\test_retriever.py" @"
# tests/unit/test_retriever.py - Owner: Ghassen
import pytest
from retrieval.hybrid_retriever import retrieve

def test_returns_list():
    assert isinstance(retrieve("What is LangGraph?", k=3), list)

def test_has_required_keys():
    result = retrieve("What is LangGraph?", k=1)
    if result:
        assert "chunk_id" in result[0]
        assert "text"     in result[0]
        assert "score"    in result[0]
"@

W "tests\unit\test_generator.py" @"
# tests/unit/test_generator.py - Owner: Mariem
import pytest
from generation.answer_generator import generate_answer

CHUNKS = [{
    "chunk_id": "lc_001",
    "text": "LangGraph is a library for building stateful agents.",
    "url": "https://docs.langchain.com/langgraph/overview",
    "framework": "langgraph", "score": 0.95
}]

def test_returns_dict():
    assert isinstance(generate_answer("What is LangGraph?", CHUNKS), dict)

def test_has_required_keys():
    r = generate_answer("What is LangGraph?", CHUNKS)
    assert "answer" in r and "sources" in r and "query" in r
"@

W "tests\unit\test_api.py" @"
# tests/unit/test_api.py - Owner: Amine
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_query_route_exists():
    res = client.post("/api/query", json={"question": "What is LangGraph?"})
    assert res.status_code in [200, 501]
"@

# eval/ - written by Aya (cross-module: touches retrieval + generation output)
W "tests\eval\questions.json" @"
[
  {"id":1,"question":"What is LangGraph?","expected_framework":"langgraph"},
  {"id":2,"question":"How does CrewAI define agents?","expected_framework":"crewai"},
  {"id":3,"question":"What is the MCP protocol?","expected_framework":"mcp"},
  {"id":4,"question":"How does AutoGen handle multi-agent communication?","expected_framework":"autogen"},
  {"id":5,"question":"How does LangChain implement tool calling?","expected_framework":"langchain"},
  {"id":6,"question":"What is function calling in OpenAI?","expected_framework":"openai"},
  {"id":7,"question":"How does Anthropic implement tool use?","expected_framework":"anthropic"},
  {"id":8,"question":"What is a transformer attention mechanism?","expected_framework":"foundational"},
  {"id":9,"question":"What is the capital of Mars?","expected_framework":null},
  {"id":10,"question":"What version of LangGraph supports memory?","expected_framework":"langgraph"}
]
"@

W "tests\eval\evaluate.py" @"
# tests/eval/evaluate.py - Cross-module owner: Aya
#
# Aya runs evaluation because she owns the end-to-end UX
# and needs to validate the full pipeline output.

import json
from retrieval.hybrid_retriever import retrieve
from generation.answer_generator import generate_answer

with open("tests/eval/questions.json") as f:
    QUESTIONS = json.load(f)

def evaluate():
    for q in QUESTIONS:
        print(f"\nQ{q['id']}: {q['question']}")
        chunks = retrieve(q["question"], k=5)
        result = generate_answer(q["question"], chunks)
        print(f"  Answer : {result['answer'][:120]}...")
        print(f"  Sources: {[s['framework'] for s in result['sources']]}")
        print(f"  Expected: {q['expected_framework']}")

if __name__ == "__main__":
    evaluate()
"@

W "tests\integration\test_pipeline.py" @"
# tests/integration/test_pipeline.py
# Everyone merges here

import pytest

def test_full_pipeline():
    from retrieval.hybrid_retriever import retrieve
    from generation.answer_generator import generate_answer

    chunks = retrieve("What is LangGraph?", k=3)
    result = generate_answer("What is LangGraph?", chunks)
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0
"@

# ══════════════════════════════════════════════════════════════════════════════
# NOTEBOOKS - each person has a primary cell + a cross-module cell
# ══════════════════════════════════════════════════════════════════════════════
W "notebooks\01_graph_exploration.ipynb" @"
{
 "cells": [
  {"cell_type":"markdown","metadata":{},"source":["# Graph Exploration\n","Primary: Oussema | Cross-module cell: Ghassen (queries)\n"]},
  {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":["# Oussema: test entity extraction\n","import jsonlines\n","from graph.entity_extractor import extract_entities\n","with jsonlines.open('data/full_corpus_clean.jsonl') as r:\n","    sample = next(iter(r))\n","print(extract_entities(sample))"]},
  {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":["# Ghassen: test Cypher query helpers\n","from graph.queries import query_related_entities\n","# print(query_related_entities(driver, 'LangGraph'))"]}
 ],
 "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},"nbformat":4,"nbformat_minor":5
}
"@

W "notebooks\02_retrieval_experiments.ipynb" @"
{
 "cells": [
  {"cell_type":"markdown","metadata":{},"source":["# Retrieval Experiments\n","Primary: Ghassen | Cross-module cell: Oussema (graph retriever)\n"]},
  {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":["# Ghassen: test FAISS retrieval\n","from retrieval.faiss_retriever import retrieve_vector\n","results = retrieve_vector('What is LangGraph?', k=5)\n","for r in results:\n","    print(r['score'], r['text'][:80])"]},
  {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":["# Oussema: test graph retrieval\n","from retrieval.graph_retriever import retrieve_graph\n","results = retrieve_graph('What is LangGraph?', k=5)\n","print(results)"]}
 ],
 "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},"nbformat":4,"nbformat_minor":5
}
"@

W "notebooks\03_generation_tests.ipynb" @"
{
 "cells": [
  {"cell_type":"markdown","metadata":{},"source":["# Generation Tests\n","Primary: Mariem | Cross-module cell: Amine (reranker)\n"]},
  {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":["# Mariem: test prompt builder\n","from generation.prompt_builder import build_prompt\n","chunks = [{'chunk_id':'c1','text':'LangGraph builds stateful agents.','url':'http://x.com','framework':'langgraph','score':0.9}]\n","print(build_prompt('What is LangGraph?', chunks))"]},
  {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":["# Amine: test reranker output\n","from generation.reranker import rerank\n","print(rerank('What is LangGraph?', chunks))"]}
 ],
 "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},"nbformat":4,"nbformat_minor":5
}
"@

W "notebooks\04_evaluation.ipynb" @"
{
 "cells": [
  {"cell_type":"markdown","metadata":{},"source":["# System Evaluation\n","Primary: Aya | All 5 compare results here\n"]},
  {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":["# Aya: run full evaluation\n","import subprocess\n","subprocess.run(['python', 'tests/eval/evaluate.py'])"]},
  {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":["# All: compare Classic vs GraphRAG vs Hybrid\n","from retrieval.faiss_retriever import retrieve_vector\n","from retrieval.graph_retriever import retrieve_graph\n","from retrieval.hybrid_retriever import retrieve\n","query = 'How does LangGraph handle state?'\n","print('Classic:', [r['chunk_id'] for r in retrieve_vector(query, k=3)])\n","print('Graph  :', [r['chunk_id'] for r in retrieve_graph(query, k=3)])\n","print('Hybrid :', [r['chunk_id'] for r in retrieve(query, k=3)])"]}
 ],
 "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},"nbformat":4,"nbformat_minor":5
}
"@

# ══════════════════════════════════════════════════════════════════════════════
# DOCS + SCRIPTS
# ══════════════════════════════════════════════════════════════════════════════
W "docs\architecture.md" @"
# Architecture - DevDoc AI

## Cross-module map
  Oussema  -> graph/ (primary)  +  retrieval/graph_retriever.py
  Ghassen  -> retrieval/ (primary)  +  graph/queries.py
  Mariem   -> generation/ (primary)  +  api/routes/query.py
  Amine    -> api/ (primary)  +  generation/reranker.py
  Aya      -> frontend/ (primary)  +  api/routes/health.py  +  tests/eval/

## Pipeline
  full_corpus_clean.jsonl
    |
    +--[Oussema]--> graph/ --> Neo4j
    |
    +--[Ghassen]--> retrieval/faiss_indexer --> FAISS index
                        |
                hybrid_retriever (FAISS + Neo4j)
                        |
                [Mariem] generation/ --> LLM answer
                        |
                [Amine]  api/ --> FastAPI
                        |
                [Aya]    frontend/ --> React UI
"@

W "docs\setup.md" @"
# Setup Guide

## Backend
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp config/.env.example config/.env
```

## Neo4j
```
docker compose up neo4j -d
```

## Build indexes (run once)
```
python -m retrieval.faiss_indexer
python -m graph.neo4j_loader
```

## Run API
```
uvicorn api.main:app --reload
```

## Run Frontend
```
cd frontend && npm install && npm run dev
```
"@

W "docs\api_reference.md" @"
# API Reference

## GET /health  (owner: Aya)
{"status": "ok", "service": "devdoc-ai"}

## POST /api/query  (owner: Mariem)
Request:  {"question": str, "top_k": 5, "use_graph": true}
Response: {"answer": str, "sources": [{url, framework, text}], "query": str}
"@

W "scripts\run_pipeline.sh" @"
#!/bin/bash
set -e
python -m retrieval.faiss_indexer
python -m graph.neo4j_loader
uvicorn api.main:app --reload
"@

W "scripts\setup_neo4j.sh" @"
#!/bin/bash
docker compose up neo4j -d
echo "Neo4j: bolt://localhost:7687  |  browser: http://localhost:7474"
"@

# ══════════════════════════════════════════════════════════════════════════════
# GIT
# ══════════════════════════════════════════════════════════════════════════════
git add .
git commit -m "Initial project structure - DevDoc AI Hybrid GraphRAG"

git checkout -b feat/graph      ; git checkout main
git checkout -b feat/retrieval  ; git checkout main
git checkout -b feat/generation ; git checkout main
git checkout -b feat/api        ; git checkout main
git checkout -b feat/frontend   ; git checkout main

Write-Host ""
Write-Host "Done! Repo created with cross-module ownership." -ForegroundColor Green
Write-Host ""
Write-Host "Oussema  -> graph/  +  retrieval/graph_retriever.py" -ForegroundColor Cyan
Write-Host "Ghassen  -> retrieval/  +  graph/queries.py" -ForegroundColor Cyan
Write-Host "Mariem   -> generation/  +  api/routes/query.py" -ForegroundColor Cyan
Write-Host "Amine    -> api/  +  generation/reranker.py" -ForegroundColor Cyan
Write-Host "Aya      -> frontend/  +  api/routes/health.py  +  tests/eval/" -ForegroundColor Cyan
Write-Host ""
git branch
