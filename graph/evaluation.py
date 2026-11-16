# graph/evaluation.py
# Owner: Aya
#
# Compare ce qu'un extracteur produit à un jeu de référence annoté à la main (gold set).
# Gold (JSONL, une ligne par chunk) :
#   {"chunk_id": "...", "entities": [{"name": "LangGraph", "type": "Framework"}],
#    "relations": [{"source": "Agent", "relation": "USES", "target": "Tool"}]}
# Appariement : noms via norm_key (insensible à la casse, aux espaces, aux alias, au pluriel),
# relations via (source, relation canonique, cible). Métriques micro-moyennées sur tous les chunks.

import json

from graph.normalize import canonical_entity_name, normalize_relation, norm_key


def load_jsonl(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _k(name):
    return norm_key(canonical_entity_name(name))


def entity_set(ext: dict) -> set:
    return {_k(e["name"]) for e in ext.get("entities", [])}


def relation_set(ext: dict) -> set:
    out = set()
    for r in ext.get("relations", []):
        rel = r.get("relation") or normalize_relation(r.get("predicate", ""), record=False)[0]
        rel = normalize_relation(rel, record=False)[0]
        out.add((_k(r["source"]), rel, _k(r["target"])))
    return out


def pair_set(rels: set) -> set:
    return {(s, t) for s, _, t in rels}


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3), "tp": tp, "fp": fp, "fn": fn}


def evaluate(pred_by_chunk: dict, gold_rows: list[dict]) -> dict:
    """pred_by_chunk = {chunk_id: {"entities": [...], "relations": [...]}}.
    Renvoie les métriques entités, relations (strict) et paires (relation ignorée : le bon lien
    a-t-il été trouvé, même mal étiqueté ?)."""
    acc = {k: [0, 0, 0] for k in ("entities", "relations", "pairs")}
    for g in gold_rows:
        pred = pred_by_chunk.get(g["chunk_id"], {"entities": [], "relations": []})
        sets = {"entities": (entity_set(pred), entity_set(g))}
        pr, gr = relation_set(pred), relation_set(g)
        sets["relations"], sets["pairs"] = (pr, gr), (pair_set(pr), pair_set(gr))
        for k, (p, t) in sets.items():
            acc[k][0] += len(p & t)
            acc[k][1] += len(p - t)
            acc[k][2] += len(t - p)
    return {k: prf(*v) for k, v in acc.items()}
