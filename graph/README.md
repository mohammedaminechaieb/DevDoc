# graph/ - Knowledge Graph
Primary owner: Oussema | Branch: feat/graph
Cross-module contribution here: Ghassen (queries.py)
Oussema contributes to: retrieval/graph_retriever.py

## Schema (NLP.pdf section 5) - see schema.py
- Nodes: Concept, Framework, Component, Technology, Technique, Chunk
- Relations: IMPLEMENTS, USES, HAS, DELEGATES_TO, CONTAINS, CONNECTS, SUPPORTS,
  ALTERNATIVE_TO, MENTIONED_IN
- Every relation stores its provenance: chunk_id, url, framework, version, confidence

## Pipeline
1. Read `full_corpus/full_corpus_clean.jsonl` (`CORPUS_PATH`)
2. entity_extractor.py - keyword/alias matching (+ spaCy) per chunk
3. relation_extractor.py - relations between entities
4. neo4j_loader.py - push chunks, entities and relations to Neo4j
5. queries.py (Ghassen) - Cypher helpers used by retrieval and agents

## Run
```
docker compose up neo4j -d
python -m graph.neo4j_loader
```
