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
`
docker compose up neo4j -d
python -m graph.neo4j_loader
`
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
