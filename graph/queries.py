# graph/queries.py
# Owner: Aya
#
# Cypher helpers used by retrieval/graph_retriever.py and agents (knowledge_retriever, GraphViewer).
# Toutes les valeurs passent en PARAMÈTRES ; seuls les types de relations du schéma (liste blanche)
# sont insérés dans le texte des requêtes.
#
#   link_entities(driver, question)            -> entités du graphe citées dans une question
#   query_entity_chunks(driver, name)          -> chunk_ids qui mentionnent l'entité
#   query_related_entities(driver, name, 2)    -> voisins à <= 2 sauts, avec distance et force du lien
#   query_subgraph(driver, [names], 1)         -> {nodes, edges} pour le frontend (GraphViewer)
#   query_chunks_for_entities(driver, keys)    -> chunks + texte pour la récupération GraphRAG
#
# Parcours : expansion en largeur côté Python, un aller-retour par saut. Les "hubs" (Agent, Tool,
# Python... présents dans des milliers de chunks) ne sont pas traversés : ils relieraient tout à tout.

import re

from graph.entity_extractor import clean_text, find_mentions
from graph.normalize import canonical_entity_name, norm_key
from graph.schema import RELATION_TYPES

ENTITY_RELS = sorted(RELATION_TYPES)          # MENTIONED_IN exclu : entité -> chunk
HUB_DF = 400                                  # entité mentionnée dans plus de N chunks = hub
_LUCENE_SPECIAL = re.compile(r'([+\-!(){}\[\]^"~*?:\\/]|&&|\|\|)')
_Q_STOP = set("what is are how does do the a an of in to for and or with on can i my me which why when "
              "use using between difference vs versus explain show give example about".split())


def entity_key(name: str) -> str:
    return norm_key(canonical_entity_name(name))


def _rows(driver, query: str, **params) -> list[dict]:
    with driver.session() as s:
        return [r.data() for r in s.run(query, **params)]


# ------------------------------------------------------------------ liaison question -> entités
def search_entities(driver, text: str, limit: int = 10) -> list[dict]:
    """Recherche plein texte (index entity_names sur name + aliases)."""
    terms = [t for t in re.findall(r"[A-Za-z0-9][\w.\-]*", text) if t.lower() not in _Q_STOP and len(t) > 2]
    if not terms:
        return []
    q = " OR ".join(_LUCENE_SPECIAL.sub(r"\\\1", t) for t in terms)
    return _rows(driver, "CALL db.index.fulltext.queryNodes('entity_names', $q) YIELD node, score "
                         "RETURN node.key AS key, node.name AS name, node.canonical_type AS type, "
                         "node.df AS df, score ORDER BY score DESC LIMIT $limit", q=q, limit=limit)


def link_entities(driver, question: str, max_entities: int = 6) -> list[dict]:
    """Entités de la question : (1) vocabulaire + alias, (2) n-grammes exacts, (3) plein texte en appoint."""
    text = clean_text(question)
    found: dict[str, dict] = {}
    for m in find_mentions(text):                                  # 1. dictionnaire (gratuit, précis)
        found.setdefault(entity_key(m["name"]), {"name": m["name"], "score": 1.0, "via": "dictionary"})
    words = re.findall(r"[A-Za-z0-9][\w.\-]*", text)              # 2. n-grammes (1..4 mots) == clé d'entité
    grams = {entity_key(" ".join(words[i:i + n])) for n in range(1, 5) for i in range(len(words) - n + 1)}
    grams = sorted(g for g in grams if len(g) > 2 and g not in _Q_STOP)
    exact = _rows(driver, "MATCH (e:Entity) WHERE e.key IN $keys "
                          "RETURN e.key AS key, e.name AS name, e.canonical_type AS type, e.df AS df",
                  keys=list(set(grams) | set(found)))
    linked = {}
    for r in exact:
        linked[r["key"]] = {**r, "score": 1.0, "via": found.get(r["key"], {}).get("via", "exact")}
    if len(linked) < max_entities:                                 # 3. plein texte, seulement les bons scores
        hits = search_entities(driver, text, limit=max_entities * 2)
        top = hits[0]["score"] if hits else 0
        for h in hits:
            if h["key"] not in linked and h["score"] >= 0.6 * top:
                linked[h["key"]] = {**h, "score": round(0.7 * h["score"] / top, 3), "via": "fulltext"}
    out = sorted(linked.values(), key=lambda e: (-e["score"], -(e.get("df") or 0)))
    return out[:max_entities]


# ------------------------------------------------------------------ voisinage
_EXPAND = (
    "MATCH (a:Entity)-[r]-(b:Entity) WHERE a.key IN $keys AND type(r) IN $rels "
    "RETURN a.key AS a, b.key AS b, b.name AS b_name, b.canonical_type AS b_type, b.df AS b_df, "
    "startNode(r).key AS src, endNode(r).key AS dst, type(r) AS relation, r.confidence AS confidence, "
    "r.support AS support, r.evidence AS evidence, r.source_chunk_id AS chunk_id "
    "ORDER BY r.confidence DESC LIMIT $limit")


def _bfs(driver, seed_keys: list[str], depth: int, limit_per_hop: int = 200, hub_df: int = HUB_DF):
    depth = max(1, min(int(depth), 3))
    seeds = _rows(driver, "MATCH (e:Entity) WHERE e.key IN $keys "
                          "RETURN e.key AS key, e.name AS name, e.canonical_type AS type, e.df AS df", keys=seed_keys)
    nodes = {s["key"]: {**s, "distance": 0, "strength": 1.0} for s in seeds}
    edges = {}
    frontier = [s["key"] for s in seeds]
    for hop in range(1, depth + 1):
        if not frontier:
            break
        nxt = []
        for r in _rows(driver, _EXPAND, keys=frontier, rels=ENTITY_RELS, limit=limit_per_hop):
            edges[(r["src"], r["relation"], r["dst"])] = {
                "source": r["src"], "target": r["dst"], "relation": r["relation"], "confidence": r["confidence"],
                "support": r["support"], "evidence": r["evidence"], "chunk_id": r["chunk_id"]}
            strength = nodes[r["a"]]["strength"] * (r["confidence"] or 0.5)
            if r["b"] not in nodes:
                nodes[r["b"]] = {"key": r["b"], "name": r["b_name"], "type": r["b_type"], "df": r["b_df"],
                                 "distance": hop, "strength": strength}
                if (r["b_df"] or 0) < hub_df:                        # on ne traverse pas les hubs
                    nxt.append(r["b"])
            elif nodes[r["b"]]["distance"] == hop:
                nodes[r["b"]]["strength"] = max(nodes[r["b"]]["strength"], strength)
        frontier = nxt
    return nodes, edges


def query_related_entities(driver, entity_name: str, depth: int = 2, limit: int = 50) -> list[dict]:
    nodes, _ = _bfs(driver, [entity_key(entity_name)], depth)
    out = [n for n in nodes.values() if n["distance"] > 0]
    out.sort(key=lambda n: (n["distance"], -n["strength"], -(n["df"] or 0)))
    return out[:limit]


def query_subgraph(driver, entity_names: list[str], depth: int = 1, max_nodes: int = 60) -> dict:
    """Format GraphViewer : nodes [{id, label, type, df, seed}], edges [{source, target, relation, ...}]."""
    nodes, edges = _bfs(driver, [entity_key(n) for n in entity_names], depth)
    keep = sorted(nodes.values(), key=lambda n: (n["distance"], -n["strength"], -(n["df"] or 0)))[:max_nodes]
    ids = {n["key"] for n in keep}
    return {"nodes": [{"id": n["key"], "label": n["name"], "type": n["type"], "df": n["df"],
                       "seed": n["distance"] == 0} for n in keep],
            "edges": [e for e in edges.values() if e["source"] in ids and e["target"] in ids]}


# ------------------------------------------------------------------ chunks
def query_entity_chunks(driver, entity_name: str, limit: int = 50) -> list[str]:
    rows = _rows(driver, "MATCH (e:Entity {key: $key})-[m:MENTIONED_IN]->(c:Chunk) "
                         "RETURN c.chunk_id AS chunk_id ORDER BY m.confidence DESC, m.count DESC LIMIT $limit",
                 key=entity_key(entity_name), limit=limit)
    return [r["chunk_id"] for r in rows]


def query_chunks_for_entities(driver, keys: list[str], limit: int = 200) -> list[dict]:
    return _rows(driver, "MATCH (e:Entity)-[m:MENTIONED_IN]->(c:Chunk) WHERE e.key IN $keys "
                         "RETURN e.key AS key, c.chunk_id AS chunk_id, c.text AS text, c.url AS url, "
                         "c.framework AS framework, m.count AS count, m.confidence AS confidence "
                         "ORDER BY m.confidence DESC, m.count DESC LIMIT $limit", keys=keys, limit=limit)
