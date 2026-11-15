# graph/merge.py
# Owner: Aya
#
# Fusionne les sorties de plusieurs extracteurs. Une entité / relation trouvée par plusieurs
# méthodes obtient une confiance plus haute (noisy-or) : l'ACCORD entre méthodes est le signal
# de qualité. `votes` = nombre de méthodes distinctes ; filtrer sur votes >= 2 augmente la
# précision au détriment du rappel.

from graph.normalize import norm_key

PRIORITY = ["dictionary", "llm", "relex", "gliner", "rules"]   # qui impose le nom/type en cas de conflit


def _noisy_or(cs):
    p = 1.0
    for c in cs:
        p *= 1 - c
    return round(1 - p, 3)


def _rank(m):
    return PRIORITY.index(m) if m in PRIORITY else len(PRIORITY)


def merge_extractions(named: dict) -> dict:
    """named = {"gliner": {"entities":[...], "relations":[...]}, "llm": {...}, ...}"""
    ents, rels = {}, {}
    for _, ext in named.items():
        for e in ext["entities"]:
            ents.setdefault(norm_key(e["name"]), []).append(e)
        for r in ext["relations"]:
            rels.setdefault((norm_key(r["source"]), r["relation"], norm_key(r["target"])), []).append(r)

    out_e = []
    for group in ents.values():
        group.sort(key=lambda e: _rank(e["method"]))
        best = dict(group[0])
        methods = sorted({e["method"] for e in group}, key=_rank)
        known = [e for e in group if e["canonical_type"] != "Unclassified"]
        best.update(canonical_type=(known[0] if known else group[0])["canonical_type"],
                    method=methods, votes=len(methods), count=sum(e["count"] for e in group),
                    confidence=_noisy_or([e["confidence"] for e in group]))
        out_e.append(best)

    out_r = []
    for group in rels.values():
        group.sort(key=lambda r: (_rank(r["extraction_method"]), -len(r["evidence"])))
        best = dict(group[0])
        methods = sorted({r["extraction_method"] for r in group}, key=_rank)
        best.update(extraction_method=methods, votes=len(methods),
                    confidence=_noisy_or([r["confidence"] for r in group]))
        out_r.append(best)
    return {"entities": out_e, "relations": out_r}


def filter_by_votes(ext: dict, k: int) -> dict:
    return {"entities": [e for e in ext["entities"] if e.get("votes", 1) >= k],
            "relations": [r for r in ext["relations"] if r.get("votes", 1) >= k]}
