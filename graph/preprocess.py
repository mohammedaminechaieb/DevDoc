# graph/preprocess.py
# Owner: Aya
#
# Tri des chunks AVANT extraction. Le corpus contient beaucoup de bruit (polices CSS, boilerplate
# arXiv, blocs de code, changelogs) : l'envoyer à GLiNER / au LLM coûte du temps et des tokens et
# produit de faux nœuds. profile_chunk() classe chaque chunk et dit s'il vaut un appel de modèle.
#
#   kind        : prose | mixed | code | changelog | boilerplate | css | short
#   informative : True pour prose / mixed -> éligible aux extracteurs "modèle" (GLiNER, LLM)
#   skip_all    : True pour css / boilerplate -> même le dictionnaire est inutile
#
# Les seuils sont des heuristiques calibrées sur full_corpus_clean.jsonl (voir tests/unit/test_preprocess.py).

import re

from graph.entity_extractor import clean_text

MIN_CHARS = 120

_STOPWORDS = frozenset(
    "the a an is are was were be been to of and or in on for with that this these those it its as at by "
    "from can will may you your we our they their not but if then when which what how also into than "
    "such each more most other any all use used using".split())

_CSS = re.compile(r"font-face|font-family|font-display|unicode-range|woff2?\b|@media|@import|\bfont-weight\b", re.I)

_BOILER_MARKERS = [re.compile(p, re.I) for p in (
    r"alphaxiv", r"catalyzex", r"dagshub", r"gotit\.pub", r"sciencecast", r"arxivlabs", r"mathjax",
    r"connected papers", r"bibliographic", r"bibtex", r"endorsers?\b", r"datacite", r"litmaps",
    r"papers with code", r"influence flower", r"recommenders and search tools",
    r"fetch the complete documentation index", r"llms\.txt")]

_SYMBOLS = set("{}[]()<>=;\"'_\\|`$#@")


def _stop_ratio(text: str) -> float:
    words = re.findall(r"[A-Za-z]+", text)
    return sum(w.lower() in _STOPWORDS for w in words) / len(words) if words else 0.0


def _symbol_ratio(text: str) -> float:
    return sum(c in _SYMBOLS for c in text) / len(text) if text else 0.0


def profile_chunk(chunk: dict) -> dict:
    """Classe un chunk. Pure fonction, aucun appel réseau."""
    text = clean_text(chunk.get("text", "")).strip()
    stop, sym = _stop_ratio(text), _symbol_ratio(text)
    base = {"chars": len(text), "stop_ratio": round(stop, 3), "symbol_ratio": round(sym, 3)}

    def out(kind: str, informative: bool = False, skip_all: bool = False) -> dict:
        return {**base, "kind": kind, "informative": informative, "skip_all": skip_all}

    if len(text) < MIN_CHARS:
        return out("short")
    if len(_CSS.findall(text)) >= 3:
        return out("css", skip_all=True)
    if sum(bool(p.search(text)) for p in _BOILER_MARKERS) >= 2:
        return out("boilerplate", skip_all=True)
    if "changelog" in (chunk.get("source_id") or "").lower():
        return out("changelog")
    if stop < 0.06 or (sym > 0.07 and stop < 0.12):
        return out("code")
    if stop >= 0.14 and sym <= 0.04:
        return out("prose", informative=True)
    return out("mixed", informative=True)
