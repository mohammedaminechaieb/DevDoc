# Agentic AI Corpus — Data Preparation Guide

Generated: 2026-11-04T14:33:13.473800Z
Total sources: 41
Total chunks (raw): 102
Total chunks (clean, quality>=0.4): 102

## Chunk Schema

| Field | Type | Description |
|---|---|---|
| chunk_id | str | MD5(source_id+start)[:12] — stable identifier |
| source_id | str | Source document key |
| url | str | Original documentation URL |
| framework | str | langgraph / crewai / autogen / langchain / mcp / openai / anthropic / foundational |
| concept | str | High-level topic within the framework |
| component | str | Specific API component or class |
| version | str | Framework version at time of writing |
| char_start | int | Character offset within the source document |
| text | str | Chunk text (normalised unicode, collapsed whitespace) |
| word_count | int | Word count of this chunk |
| char_count | int | Character count of this chunk |
| has_code | bool | True if chunk contains code blocks or Python syntax |
| language | str | Detected language (always "en" for this corpus) |
| quality_score | float | 0-1 heuristic: uniqueness ratio + sentence completeness |
| dedup_hash | str | MD5(text)[:16] — use for exact deduplication |
| cleaned | bool | True — text has been unicode-normalised and whitespace-collapsed |

## Files

| File | Description |
|---|---|
| corpus_to_clean.jsonl | All chunks with full cleaning metadata |
| corpus_clean.jsonl | Filtered: quality_score >= 0.4 |
| corpus_langgraph.txt | LangGraph chunks in readable TXT format |
| corpus_crewai.txt | CrewAI chunks |
| corpus_autogen.txt | AutoGen chunks |
| corpus_langchain.txt | LangChain chunks |
| corpus_mcp.txt | MCP chunks |
| corpus_openai.txt | OpenAI function calling chunks |
| corpus_anthropic.txt | Anthropic tool use chunks |
| corpus_foundational.txt | ReAct, CoT, Reflexion papers |
| knowledge_graph_triples.json | 54 KG triples for Neo4j import |
| source_manifest.json | Per-source metadata and chunk counts |

## Recommended Data Prep Pipeline

1. Load corpus_to_clean.jsonl
2. Deduplication: group by dedup_hash, keep one per group
3. Quality filter: drop chunks where quality_score < 0.3
4. Length filter: drop chunks where word_count < 25 or word_count > 200
5. Language detection: verify language == "en"
6. Code separation: split has_code=True chunks into a code corpus
7. Embed and index: use corpus_clean.jsonl for FAISS ingestion
8. KG import: use knowledge_graph_triples.json for Neo4j import

## FAISS Ingestion

```python
import json
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

chunks = [json.loads(l) for l in open("corpus_clean.jsonl")]
docs = [
    Document(
        page_content=c["text"],
        metadata={k: v for k, v in c.items() if k != "text"}
    )
    for c in chunks
]
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.from_documents(docs, embeddings)
vectorstore.save_local("faiss_index")
```

## Neo4j KG Import

```python
import json
from langchain_community.graphs import Neo4jGraph

graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="password")
triples = json.load(open("knowledge_graph_triples.json"))
for t in triples:
    graph.query(
        "MERGE (s:Entity {id: $s}) MERGE (o:Entity {id: $o}) "
        "MERGE (s)-[r:`" + t["predicate"] + "` {source: $src}]->(o)",
        {"s": t["subject"], "o": t["object"], "src": t["source"]}
    )
```
