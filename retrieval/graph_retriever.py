# retrieval/graph_retriever.py
# Owner: Aya
#
# Récupération GraphRAG : question -> entités du graphe -> voisinage -> chunks classés.
# Contrat (retrieval/hybrid_retriever.py) : [{chunk_id, text, url, framework, score}], score dans [0, 1].
#
# Score d'un chunk = somme, sur les entités qu'il mentionne, de
#     poids_entité x confiance_mention x (1 + log(1 + occurrences))
#   poids_entité = score de liaison (entité citée dans la question) ou 0.5 x force du lien (voisin)
# + bonus si le chunk est la PREUVE d'une relation entre ces entités (le cœur de GraphRAG : un chunk
#   qui relie deux concepts de la question vaut plus qu'un chunk qui en cite un seul).
# Les entités très fréquentes (hubs) pèsent moins (idf).
# Neo4j indisponible ou graphe vide -> [] et un avertissement : la recherche vectorielle prend le relais.

import logging
import math

from graph import queries as Q

log = logging.getLogger(__name__)
_driver = None
NEIGHBOR_WEIGHT = 0.5
EVIDENCE_BONUS = 0.5


def get_driver():
    global _driver
    if _driver is None:
        from graph.neo4j_loader import get_driver as make
        _driver = make()
    return _driver


def close():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def _idf(df) -> float:
    return 1.0 / (1.0 + math.log1p(max((df or 1) - 1, 0) / 50))


def rank_chunks(linked: list[dict], nodes: dict, edges: dict, rows: list[dict], k: int) -> list[dict]:
    """Pure fonction (testable sans Neo4j)."""
    weight = {}
    for n in nodes.values():
        base = 1.0 if n["distance"] == 0 else NEIGHBOR_WEIGHT * n.get("strength", 0.5)
        weight[n["key"]] = base * _idf(n.get("df"))
    for e in linked:
        if e["key"] in weight:
            weight[e["key"]] *= e.get("score", 1.0)
    evidence_chunks = {}
    for e in edges.values():
        if e.get("chunk_id"):
            evidence_chunks[e["chunk_id"]] = evidence_chunks.get(e["chunk_id"], 0) + (e.get("confidence") or 0.5)

    chunks = {}
    for r in rows:
        c = chunks.setdefault(r["chunk_id"], {"chunk_id": r["chunk_id"], "text": r["text"], "url": r["url"],
                                              "framework": r["framework"], "score": 0.0, "entities": []})
        c["score"] += weight.get(r["key"], 0) * (r.get("confidence") or 0.5) * (1 + math.log1p(r.get("count") or 1))
        c["entities"].append(r["key"])
    for cid, bonus in evidence_chunks.items():
        if cid in chunks:
            chunks[cid]["score"] += EVIDENCE_BONUS * bonus
    ranked = sorted(chunks.values(), key=lambda c: -c["score"])[:k]
    top = ranked[0]["score"] if ranked else 1.0
    for c in ranked:
        c["score"] = round(c["score"] / top, 4) if top else 0.0
    return ranked


def retrieve_graph(query: str, k: int = 5, depth: int = 1, driver=None) -> list[dict]:
    """Returns: [{chunk_id, text, url, framework, score, entities}]"""
    try:
        from neo4j.exceptions import DriverError, Neo4jError
    except ImportError:                                            # pragma: no cover
        DriverError = Neo4jError = Exception
    try:
        drv = driver or get_driver()
        linked = Q.link_entities(drv, query)
        if not linked:
            return []
        nodes, edges = Q._bfs(drv, [e["key"] for e in linked], depth)
        rows = Q.query_chunks_for_entities(drv, list(nodes), limit=max(50, 20 * k))
        return rank_chunks(linked, nodes, edges, rows, k)
    except (DriverError, Neo4jError, OSError) as e:
        log.warning("graph retrieval indisponible (%s: %s) - FAISS seul", type(e).__name__, e)
        return []


def retrieve_subgraph(query: str, depth: int = 1, max_nodes: int = 40, driver=None) -> dict:
    """{nodes, edges} autour des entités de la question, pour state["graph"] / le GraphViewer."""
    try:
        drv = driver or get_driver()
        names = [e["name"] for e in Q.link_entities(drv, query)]
        return Q.query_subgraph(drv, names, depth, max_nodes) if names else {"nodes": [], "edges": []}
    except Exception as e:                                         # noqa: BLE001 - l'UI ne doit pas casser
        log.warning("sous-graphe indisponible (%s: %s)", type(e).__name__, e)
        return {"nodes": [], "edges": []}
