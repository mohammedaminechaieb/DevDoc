# graph/normalize.py
# Owner: Aya
#
# Normalisation = ce qui rend plusieurs extracteurs COMPARABLES et FUSIONNABLES :
#   - noms d'entités  : "State Graph" / "StateGraph" / "state graphs" -> une seule clé
#   - types de nœuds  : "library" -> Framework ; inconnu -> Unclassified (raw_type conservé)
#   - prédicats       : "relies on" -> USES ; inconnu -> RELATED_TO (raw_predicate conservé)
# Les types/prédicats inconnus sont comptés dans CANDIDATES : c'est la liste à relire
# pour décider d'étendre le schéma (politique "candidats, pas erreurs").

import json
import re
from collections import Counter
from pathlib import Path

from graph import vocabulary as V
from graph.schema import NODE_TYPES, RELATION_TYPES, UNKNOWN_NODE_TYPE, UNKNOWN_RELATION_TYPE

CANDIDATES = {"node_type": Counter(), "relation": Counter()}


def norm_key(name: str) -> str:
    """Clé de comparaison : minuscules, sans espaces/tirets, pluriel simple retiré."""
    s = re.sub(r"[\s\-_./]+", "", (name or "").lower())
    if len(s) > 3 and s.endswith("s") and not s.endswith("ss"):
        s = s[:-1]
    return s


# ---------- entités ----------
_ALIAS_BY_KEY = {norm_key(a): c for a, c in V.ALIASES.items()}
_ALIAS_BY_KEY.update({norm_key(c): c for c in V.ENTITIES})


def canonical_entity_name(name: str) -> str:
    """Résolution d'entité : alias -> nom canonique ; sinon le nom nettoyé tel quel."""
    clean = re.sub(r"\s+", " ", (name or "").strip())
    clean = clean.strip("`'\"“”‘’.,;:!?")            # guillemets / backticks / ponctuation collée
    clean = re.sub(r"\(\s*\)$", "", clean).strip()     # "create_agent()" -> "create_agent"
    stripped = re.sub(r"^(?:the|a|an)\s+", "", clean, flags=re.IGNORECASE)
    clean = stripped or clean                          # "the Agent" -> "Agent"
    return _ALIAS_BY_KEY.get(norm_key(clean), clean)


# ---------- types de nœuds ----------
TYPE_SYNONYMS = {
    "library": "Framework", "sdk": "Framework", "package": "Framework", "framework": "Framework",
    "ai agent": "Agent", "language model": "Model", "llm": "Model", "large language model": "Model",
    "function": "Tool", "database": "DataStore", "vector database": "DataStore", "vector store": "DataStore",
    "data structure": "DataStructure", "programming language": "Language", "query language": "Language",
    "pattern": "Technique", "method": "Technique", "algorithm": "Technique", "strategy": "Technique",
    "class": "Component", "module": "Component", "service": "Platform", "product": "Platform",
    "benchmark": "Dataset", "prompt": "Artifact",
}
_TYPE_BY_LOWER = {t.lower(): t for t in NODE_TYPES}


def normalize_type(raw: str, record: bool = True) -> str:
    """Type brut -> type canonique du schéma, ou Unclassified (le brut reste dans raw_type)."""
    key = (raw or "").strip().lower()
    if key in _TYPE_BY_LOWER:
        return _TYPE_BY_LOWER[key]
    if key in TYPE_SYNONYMS:
        return TYPE_SYNONYMS[key]
    if record and key:
        CANDIDATES["node_type"][key] += 1
    return UNKNOWN_NODE_TYPE


# ---------- prédicats ----------
# verbe/expression (forme de base) -> relation canonique
PREDICATE_SYNONYMS = {
    "use": "USES", "utilize": "USES", "utilise": "USES", "leverage": "USES", "employ": "USES",
    "rely on": "USES", "work with": "USES",
    "call": "INVOKES", "invoke": "INVOKES", "execute": "INVOKES", "trigger call": "INVOKES",
    "have": "HAS", "has": "HAS", "maintain": "HAS", "hold": "HAS", "keep": "HAS",
    "contain": "CONTAINS", "include": "CONTAINS", "consist of": "CONTAINS", "comprise": "CONTAINS",
    "part of": "PART_OF", "belong to": "PART_OF", "is part of": "PART_OF",
    "depend on": "DEPENDS_ON", "require": "REQUIRES", "need": "REQUIRES",
    "implement": "IMPLEMENTS", "is built on": "IMPLEMENTS", "build on": "IMPLEMENTS",
    "extend": "EXTENDS", "inherit from": "INHERITS_FROM", "subclass": "INHERITS_FROM",
    "communicate with": "COMMUNICATES_WITH", "exchange message with": "COMMUNICATES_WITH",
    "connect to": "CONNECTS_TO", "connect": "CONNECTS_TO", "expose": "CONNECTS_TO", "bridge": "CONNECTS_TO",
    "delegate to": "DELEGATES_TO", "hand off to": "DELEGATES_TO", "transfer to": "DELEGATES_TO",
    "collaborate with": "COLLABORATES_WITH", "work together with": "COLLABORATES_WITH",
    "support": "SUPPORTS", "provide": "PROVIDES", "offer": "PROVIDES",
    "enable": "ENABLES", "allow": "ENABLES",
    "store": "STORES", "persist": "STORES", "save": "STORES",
    "retrieve": "RETRIEVES", "fetch": "RETRIEVES", "query": "RETRIEVES",
    "generate": "GENERATES", "produce": "GENERATES", "create": "GENERATES",
    "transform": "TRANSFORMS", "convert": "TRANSFORMS",
    "route to": "ROUTES_TO", "route": "ROUTES_TO", "trigger": "TRIGGERS", "validate": "VALIDATES",
    "evaluate": "EVALUATES", "measure": "MEASURES", "optimize": "OPTIMIZES", "optimise": "OPTIMIZES",
    "alternative to": "ALTERNATIVE_TO", "instead of": "ALTERNATIVE_TO", "replace": "ALTERNATIVE_TO",
    "similar to": "SIMILAR_TO", "contrast with": "CONTRASTS_WITH", "unlike": "CONTRASTS_WITH",
}
_AUX = re.compile(r"^(?:is|are|can|will|may|also|then)\s+")


def _stems(first: str):
    yield first
    if first.endswith("ing"):
        yield first[:-3]
        yield first[:-3] + "e"
    if first.endswith("ed"):
        yield first[:-2]
        yield first[:-1]
    if first.endswith("ies"):
        yield first[:-3] + "y"      # relies -> rely
    if first.endswith("ied"):
        yield first[:-3] + "y"
    if first.endswith("es"):
        yield first[:-2]
    if first.endswith("s"):
        yield first[:-1]


def normalize_relation(raw: str, record: bool = True):
    """Prédicat brut -> (relation canonique, connue ?). Inconnu -> (RELATED_TO, False)."""
    s = re.sub(r"\s+", " ", (raw or "").lower().replace("_", " ")).strip()
    s = _AUX.sub("", s) if s not in PREDICATE_SYNONYMS else s
    direct = s.upper().replace(" ", "_")
    if direct in RELATION_TYPES and direct != UNKNOWN_RELATION_TYPE:
        return direct, True
    words = s.split()
    if words:
        for stem in _stems(words[0]):
            cand = " ".join([stem] + words[1:])
            if cand in PREDICATE_SYNONYMS:
                return PREDICATE_SYNONYMS[cand], True
    if record and s:
        CANDIDATES["relation"][s] += 1
    return UNKNOWN_RELATION_TYPE, False


def write_candidates(path) -> int:
    """Écrit les types/prédicats inconnus (avec fréquence) pour relecture humaine."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"kind": k, "raw": raw, "count": c}
            for k, counter in CANDIDATES.items() for raw, c in counter.most_common()]
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)
