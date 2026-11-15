# graph/ - Knowledge Graph
Owner: Aya | Branch: feat/graph
Aya also owns: retrieval/graph_retriever.py

## Schema - see schema.py (hybrid open-world)
- 18 node types (NODE_TYPES) + Chunk, ~35 relation types (RELATION_TYPES) + MENTIONED_IN
- Unknown types/predicates are kept as candidates (raw_type / raw_predicate), mapped to
  Unclassified / RELATED_TO, and listed in data/graph/review/candidates.jsonl for review
- Every relation stores its provenance: source_chunk_id, source_url, document_version,
  evidence, extraction_method, raw_predicate, confidence (+ support, chunk_ids, type_ok)

## Extraction approach - hybrid cascade (cheapest first, most precise last)
| step | module | runs on | role |
|---|---|---|---|
| 0. triage | preprocess.py | all chunks | CSS / arXiv boilerplate skipped; code & changelogs: dictionary only |
| 1. anchors | extractors/dictionary.py (entity_extractor + relation_extractor, vocabulary.py) | useful chunks | high-precision known entities + rule relations |
| 2. recall | extractors/gliner_extractor.py (GLiNER, zero-shot on the 18 types) | informative chunks | discovers entities outside the vocabulary |
| 3. relations | extractors/llm_extractor.py, **guided** by steps 1-2 | informative chunks with >= 2 candidates, densest first, within `--llm-max-chunks` | typed relations; evidence must be found verbatim in the chunk and contain both ends |
| 4. fusion | merge.py | per chunk | agreement between methods -> confidence (noisy-or), `votes` |
| 5. resolution | resolution.py | whole corpus | aliases, acronyms (RAG ~ Retrieval-Augmented Generation), near-duplicates; ambiguous cases -> review |
| 6. validation | validate.py | whole corpus | entity-name filters, type constraints per relation (penalty), thresholds, evidence required |
| 7. aggregation | pipeline.py | whole corpus | one node per entity, one edge per (source, RELATION, target) with best evidence + support |

Optional: extractors/relex_extractor.py (GLiNER-Relex, entities + relations in one pass) via `--profile max`.
Compare everything on a hand-checked gold set before choosing: evaluation.py,
scripts/make_gold_sample.py, scripts/evaluate_extractors.py (P/R/F1, LLM in guided mode by default).

## Run
~~~
pip install -r graph/requirements-extraction.txt      # gliner, groq, rapidfuzz...
python -m graph.pipeline --estimate                    # how many chunks / tokens the LLM step needs
python -m graph.pipeline                               # profile "quality" -> data/graph/
python -m graph.pipeline --llm-max-chunks 300          # LLM budget per run; re-run = resume
python -m graph.pipeline --profile standard            # no LLM (local, free)

docker compose up neo4j -d
python -m graph.neo4j_loader                           # --reset to empty the database first
~~~
### Everything in Docker
~~~
docker compose -f docker-compose.yml -f docker-compose.graph.yml build graph
docker compose -f docker-compose.yml -f docker-compose.graph.yml run --rm graph
~~~
Runs the pipeline then the loader against the `neo4j` service. Options through
`-e PIPELINE_ARGS="--llm-max-chunks 350"` / `-e LOADER_ARGS="--reset"`; see docker-compose.graph.yml.

Profiles: `fast` (dictionary) | `standard` (+ GLiNER) | `quality` (+ guided LLM, default) | `max` (+ Relex).
An unavailable extractor (package or API key missing) is skipped with a warning and recorded in
`data/graph/manifest.json` (`--strict` makes it an error). Raw outputs are appended to
`data/graph/raw/<extractor>.jsonl` and LLM answers cached in `data/cache/`: an interrupted run
(quota, Ctrl+C) resumes where it stopped.

LLM settings (config/.env): `LLM_PROVIDER` (groq | ollama), `GRAPH_LLM_MODEL` (extraction model,
defaults to `LLM_MODEL`), `LLM_RPM` (requests/minute, default 25).

## Outputs (data/graph/)
- entities.jsonl, relations.jsonl, mentions.jsonl - what the loader pushes to Neo4j
- manifest.json - extractors used/skipped, counts, policy, LLM stats, incomplete runs
- review/merge_suggestions.jsonl - doubtful merges (acronyms, near-duplicates) to check by hand
- review/candidates.jsonl - out-of-schema types/predicates (schema extension candidates)
- review/vocabulary_suggestions.jsonl - frequent entities to add to vocabulary.py

## Neo4j model
`(:Entity:<Type> {key, name, aliases, ...})-[:<RELATION> {confidence, evidence, ...}]->(:Entity)`,
`(:Entity)-[:MENTIONED_IN]->(:Chunk {chunk_id, text, url, framework, ...})`.
Constraints on Entity.key / Chunk.chunk_id, full-text index `entity_names` (name + aliases).

## Queries (queries.py) - used by retrieval/graph_retriever.py and the agents
- `link_entities(driver, question)` - entities named in a question (vocabulary, exact n-grams, full-text)
- `query_related_entities`, `query_entity_chunks`, `query_subgraph` (GraphViewer format `{nodes, edges}`)
- `retrieval.graph_retriever.retrieve_graph(query, k)` -> `[{chunk_id, text, url, framework, score}]`;
  `retrieve_subgraph(query)` for `state["graph"]`. Neo4j down -> `[]` + warning (FAISS takes over).
