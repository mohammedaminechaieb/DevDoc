# graph/extractors/base.py
# Owner: Aya
#
# FORMAT COMMUN : tous les extracteurs (dictionnaire, GLiNER, GLiNER-Relex, LLM...) renvoient
#   {"entities": [Entity], "relations": [Relation]}
# ce qui permet de les comparer et de les fusionner sans réécrire le reste.
#
# Entity   = {name, canonical_type, raw_type, chunk_id, count, confidence, method}
# Relation = {source, target, relation, raw_predicate, evidence, source_chunk_id, source_url,
#             document_version, extraction_method, confidence, source_type, target_type}
# (les noms de champs suivent graph/schema.py : NODE_PROPERTIES / RELATION_PROPERTIES)

import re
from typing import Protocol

from graph.normalize import canonical_entity_name, normalize_relation, normalize_type


class Extractor(Protocol):
    name: str

    def extract(self, chunk: dict) -> dict: ...


def empty() -> dict:
    return {"entities": [], "relations": []}


def make_entity(name: str, raw_type: str, chunk: dict, method: str,
                confidence: float = 1.0, count: int = 1) -> dict:
    return {"name": canonical_entity_name(name), "canonical_type": normalize_type(raw_type),
            "raw_type": raw_type, "chunk_id": chunk.get("chunk_id"), "count": count,
            "confidence": round(float(confidence), 3), "method": method}


def make_relation(source: str, target: str, raw_predicate: str, chunk: dict, method: str,
                  confidence: float, evidence: str, source_type: str = "", target_type: str = "",
                  relation: str | None = None) -> dict:
    canon = relation or normalize_relation(raw_predicate)[0]
    return {"source": canonical_entity_name(source), "target": canonical_entity_name(target),
            "relation": canon, "raw_predicate": raw_predicate, "evidence": (evidence or "").strip()[:300],
            "source_chunk_id": chunk.get("chunk_id"), "source_url": chunk.get("url"),
            "document_version": chunk.get("version"), "extraction_method": method,
            "confidence": round(float(confidence), 3),
            "source_type": normalize_type(source_type, record=False) if source_type else "",
            "target_type": normalize_type(target_type, record=False) if target_type else ""}


_SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def windows(text: str, max_chars: int = 1200):
    """Découpe un long texte en fenêtres (offset, texte) coupées aux frontières de phrases.
    Les modèles encodeurs (GLiNER...) ont une longueur maximale : on ne leur donne jamais un chunk entier."""
    out, buf, start, pos = [], "", 0, 0
    for sent in _SENT.split(text):
        idx = text.find(sent, pos)
        pos = idx + len(sent) if idx >= 0 else pos
        if buf and len(buf) + len(sent) + 1 > max_chars:
            out.append((start, buf))
            buf, start = "", idx
        if not buf:
            start = idx if idx >= 0 else start
        buf = f"{buf} {sent}".strip() if buf else sent
    if buf:
        out.append((start, buf))
    return out


def sentence_with(window: str, *terms: str) -> str:
    """Phrase de `window` qui contient tous les `terms` (sinon l'un d'eux, sinon le début)."""
    sents = [s for s in _SENT.split(window) if s.strip()]
    low = [t.lower() for t in terms if t]
    for s in sents:
        if all(t in s.lower() for t in low):
            return s.strip()
    for s in sents:
        if any(t in s.lower() for t in low):
            return s.strip()
    return window[:300].strip()
