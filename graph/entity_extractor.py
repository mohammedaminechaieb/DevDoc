# graph/entity_extractor.py
# Owner: Aya
#
# Extracteur d'ENTITÉS par dictionnaire (vocabulaire : graph/vocabulary.py).
# Rapide, gratuit, déterministe : c'est la base de comparaison des autres extracteurs.
# Input : chunk dict {chunk_id, text, framework, ...}
# Output: list[Entity]  (voir graph/extractors/base.py)

import re

from graph import vocabulary as V
from graph.extractors.base import make_entity

# marqueurs de nettoyage laissés dans le corpus
_NOISE = re.compile(r"\b(?:CODE_?BLOCK|INLINE_?CODE)\b")


def clean_text(text: str) -> str:
    return _NOISE.sub(" ", text or "")


def _build_patterns():
    forms = {name: {name} for name in V.ENTITIES}
    for surface, canon in V.ALIASES.items():
        if canon in forms:
            forms[canon].add(surface)
    patterns = []
    for canon, surfaces in forms.items():
        alts = "|".join(re.escape(s) for s in sorted(surfaces, key=len, reverse=True))
        flags = 0 if canon in V.CASE_SENSITIVE else re.IGNORECASE
        # mots entiers, pluriel simple accepté, "Node.js" exclu
        rx = re.compile(rf"(?<![A-Za-z0-9])(?:{alts})(?:s|es)?(?![A-Za-z0-9]|\.js)", flags)
        patterns.append((canon, V.ENTITIES[canon], rx))
    return patterns


_PATTERNS = _build_patterns()


def find_mentions(text: str) -> list[dict]:
    """Toutes les occurrences avec position : [{name, type, start, end}] (sert aux relations)."""
    out = [{"name": n, "type": t, "start": m.start(), "end": m.end()}
           for n, t, rx in _PATTERNS for m in rx.finditer(text)]
    return sorted(out, key=lambda m: m["start"])


def extract_entities(chunk: dict) -> list[dict]:
    text = clean_text(chunk.get("text", ""))
    found = {}
    for name, etype, rx in _PATTERNS:
        n = len(rx.findall(text))
        if n:
            found[(name, etype)] = n
    # le framework du chunk (métadonnée) est toujours une entité du chunk
    meta = V.FRAMEWORK_META.get(chunk.get("framework", ""))
    if meta:
        found.setdefault(meta, 0)
    return [make_entity(n, t, chunk, "dictionary", confidence=1.0, count=c)
            for (n, t), c in sorted(found.items(), key=lambda kv: -kv[1])]
