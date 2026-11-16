# graph/neo4j_loader.py
# Owner: Aya
#
# Charge data/graph/*.jsonl (produits par graph/pipeline.py) dans Neo4j. Idempotent (MERGE) et par lots.
#
#   docker compose up neo4j -d
#   python -m graph.pipeline            # extraction (une fois, reprenable)
#   python -m graph.neo4j_loader        # chargement
#   python -m graph.neo4j_loader --reset   # vide la base avant (après un changement de schéma)
#
# Modèle dans Neo4j :
#   (:Chunk {chunk_id, url, document, section, framework, concept, component, version, text})
#   (:Entity:<Type> {key, name, canonical_type, raw_types, aliases, count, df, confidence, votes,
#                    methods, frameworks, source_documents})        <Type> = un NODE_TYPES ou Unclassified
#   (:Entity)-[:MENTIONED_IN {count, confidence, methods}]->(:Chunk)
#   (:Entity)-[:<RELATION> {confidence, support, evidence, source_chunk_id, source_url, document_version,
#                           extraction_method, raw_predicate, raw_predicates, chunk_ids, type_ok}]->(:Entity)
# Labels et types de relations ne peuvent pas être des paramètres Cypher : ils sont insérés dans la
# requête UNIQUEMENT s'ils appartiennent au schéma (liste blanche), sinon Unclassified / RELATED_TO.

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

from config.settings import CORPUS_PATH, NEO4J_PASS, NEO4J_URI, NEO4J_USER, ROOT
from graph.schema import (CHUNK_LABEL, NODE_TYPES, PROVENANCE_RELATION, RELATION_TYPES, UNKNOWN_NODE_TYPE,
                          UNKNOWN_RELATION_TYPE)

ENTITY_LABEL = "Entity"
TYPE_LABELS = sorted(NODE_TYPES) + [UNKNOWN_NODE_TYPE]
BATCH = 500

SCHEMA_STATEMENTS = [
    f"CREATE CONSTRAINT entity_key IF NOT EXISTS FOR (e:{ENTITY_LABEL}) REQUIRE e.key IS UNIQUE",
    f"CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:{CHUNK_LABEL}) REQUIRE c.chunk_id IS UNIQUE",
    f"CREATE INDEX entity_type IF NOT EXISTS FOR (e:{ENTITY_LABEL}) ON (e.canonical_type)",
    f"CREATE INDEX chunk_framework IF NOT EXISTS FOR (c:{CHUNK_LABEL}) ON (c.framework)",
    f"CREATE FULLTEXT INDEX entity_names IF NOT EXISTS FOR (e:{ENTITY_LABEL}) ON EACH [e.name, e.aliases]",
]


def get_driver():
    from neo4j import GraphDatabase
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))


def wait_for(driver, seconds: int = 60):
    """Neo4j met ~20 s à démarrer dans Docker : on réessaie au lieu d'échouer tout de suite."""
    deadline = time.time() + seconds
    while True:
        try:
            driver.verify_connectivity()
            return
        except Exception as e:                                  # noqa: BLE001
            if time.time() > deadline:
                raise SystemExit(f"Neo4j injoignable sur {NEO4J_URI} ({type(e).__name__}: {e}).\n"
                                 "Lance d'abord : docker compose up neo4j -d") from e
            time.sleep(2)


def _batches(rows, size=BATCH):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def _write(driver, query: str, rows: list[dict], size: int = BATCH) -> int:
    with driver.session() as s:
        for b in _batches(rows, size):
            s.execute_write(lambda tx, b=b: tx.run(query, rows=b).consume())
    return len(rows)


def safe_label(t: str) -> str:
    return t if t in NODE_TYPES else UNKNOWN_NODE_TYPE


def safe_relation(r: str) -> str:
    return r if r in RELATION_TYPES else UNKNOWN_RELATION_TYPE


# ------------------------------------------------------------------ schéma / remise à zéro
def create_schema(driver):
    with driver.session() as s:
        for q in SCHEMA_STATEMENTS:
            s.run(q).consume()


def reset(driver, batch: int = 10_000) -> int:
    total = 0
    with driver.session() as s:
        while True:
            n = s.run("MATCH (n) WITH n LIMIT $n DETACH DELETE n RETURN count(*) AS c", n=batch).single()["c"]
            total += n
            if n == 0:
                return total


# ------------------------------------------------------------------ chargement
def chunk_row(chunk: dict) -> dict:
    return {"chunk_id": chunk["chunk_id"], "url": chunk.get("url"), "document": chunk.get("source_id"),
            "section": chunk.get("concept"), "framework": chunk.get("framework"),
            "concept": chunk.get("concept"), "component": chunk.get("component"),
            "version": chunk.get("version"), "text": chunk.get("text", "")}


def load_chunks(driver, chunks: list[dict]) -> int:
    q = (f"UNWIND $rows AS row MERGE (c:{CHUNK_LABEL} {{chunk_id: row.chunk_id}}) "
         "SET c.url = row.url, c.document = row.document, c.section = row.section, c.framework = row.framework, "
         "c.concept = row.concept, c.component = row.component, c.version = row.version, c.text = row.text")
    return _write(driver, q, [chunk_row(c) for c in chunks])


ENTITY_PROPS = ("name", "canonical_type", "raw_types", "aliases", "description", "count", "df", "confidence",
                "votes", "methods", "frameworks", "source_documents")


def load_entities(driver, entities: list[dict]) -> int:
    by_label = defaultdict(list)
    for e in entities:
        by_label[safe_label(e["canonical_type"])].append(
            {"key": e["key"], "props": {k: e.get(k) for k in ENTITY_PROPS}})
    remove_all = ":".join(f"`{t}`" for t in TYPE_LABELS)
    for label, rows in by_label.items():           # label issu de la liste blanche -> insertion sûre
        q = (f"UNWIND $rows AS row MERGE (e:{ENTITY_LABEL} {{key: row.key}}) "
             f"REMOVE e:{remove_all} SET e:`{label}` SET e += row.props")
        _write(driver, q, rows)
    return len(entities)


def load_mentions(driver, mentions: list[dict]) -> int:
    q = (f"UNWIND $rows AS row MATCH (e:{ENTITY_LABEL} {{key: row.entity_key}}) "
         f"MATCH (c:{CHUNK_LABEL} {{chunk_id: row.chunk_id}}) "
         f"MERGE (e)-[m:{PROVENANCE_RELATION}]->(c) "
         "SET m.count = row.count, m.confidence = row.confidence, m.methods = row.methods")
    return _write(driver, q, mentions)


REL_PROPS = ("confidence", "support", "evidence", "source_chunk_id", "source_url", "document_version",
             "extraction_method", "raw_predicate", "raw_predicates", "chunk_ids", "type_ok", "type_issue")


def load_relations(driver, relations: list[dict]) -> int:
    by_type = defaultdict(list)
    for r in relations:
        by_type[safe_relation(r["relation"])].append(
            {"s": r["source_key"], "t": r["target_key"], "props": {k: r.get(k) for k in REL_PROPS}})
    for rel, rows in by_type.items():
        q = (f"UNWIND $rows AS row MATCH (s:{ENTITY_LABEL} {{key: row.s}}) MATCH (t:{ENTITY_LABEL} {{key: row.t}}) "
             f"MERGE (s)-[r:`{rel}`]->(t) SET r += row.props")
        _write(driver, q, rows)
    return len(relations)


# compatibilité avec l'ancienne interface (un chunk à la fois)
def load_chunk(driver, chunk: dict):
    return load_chunks(driver, [chunk])


# ------------------------------------------------------------------ lecture des exports
def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def read_graph(data_dir: Path) -> dict:
    missing = [n for n in ("entities", "relations", "mentions") if not (data_dir / f"{n}.jsonl").exists()]
    if missing:
        raise SystemExit(f"{data_dir} ne contient pas {missing}. Lance d'abord : python -m graph.pipeline")
    return {n: read_jsonl(data_dir / f"{n}.jsonl") for n in ("entities", "relations", "mentions")}


def load_all(driver, graph: dict, corpus_path=CORPUS_PATH, all_chunks: bool = False, verbose=True) -> dict:
    import jsonlines
    needed = {m["chunk_id"] for m in graph["mentions"]}
    with jsonlines.open(corpus_path) as r:
        chunks = [c for c in r if all_chunks or c["chunk_id"] in needed]
    create_schema(driver)
    counts = {"chunks": load_chunks(driver, chunks), "entities": load_entities(driver, graph["entities"]),
              "mentions": load_mentions(driver, graph["mentions"]),
              "relations": load_relations(driver, graph["relations"])}
    if verbose:
        print("chargé :", counts)
    return counts


def summary(driver) -> dict:
    with driver.session() as s:
        labels = {r["label"]: r["n"] for r in s.run(
            f"MATCH (e:{ENTITY_LABEL}) RETURN e.canonical_type AS label, count(*) AS n ORDER BY n DESC")}
        rels = {r["t"]: r["n"] for r in s.run("MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS n ORDER BY n DESC")}
        chunks = s.run(f"MATCH (c:{CHUNK_LABEL}) RETURN count(c) AS n").single()["n"]
    return {"chunks": chunks, "entities_by_type": labels, "relations_by_type": rels}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Charge data/graph/ dans Neo4j")
    ap.add_argument("--data-dir", default=str(ROOT / "data" / "graph"))
    ap.add_argument("--reset", action="store_true", help="vide la base avant le chargement")
    ap.add_argument("--all-chunks", action="store_true", help="charge aussi les chunks sans entité")
    ap.add_argument("--wait", type=int, default=60, help="secondes d'attente du démarrage de Neo4j")
    a = ap.parse_args(argv)

    data_dir = Path(a.data_dir)
    graph = read_graph(data_dir)
    manifest = data_dir / "manifest.json"
    if manifest.exists():
        m = json.loads(manifest.read_text(encoding="utf-8"))
        print(f"extraction du {m['created_at']} | extracteurs : {m['extractors_used']}"
              + (f" | ignorés : {list(m['extractors_skipped'])}" if m.get("extractors_skipped") else ""))
    driver = get_driver()
    try:
        wait_for(driver, a.wait)
        if a.reset:
            print("supprimé :", reset(driver), "nœuds")
        load_all(driver, graph, all_chunks=a.all_chunks)
        print(json.dumps(summary(driver), indent=2, ensure_ascii=False))
    finally:
        driver.close()


if __name__ == "__main__":
    main()
