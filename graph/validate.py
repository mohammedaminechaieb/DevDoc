# graph/validate.py
# Owner: Aya
#
# Garde-fous de qualité appliqués à TOUTES les méthodes d'extraction :
#   1. is_valid_entity_name() : rejette pronoms, mots génériques, URL, chemins, variables d'env,
#                               versions, identifiants internes de SDK (ResponseNewParamsInputUnion...)
#   2. check_relation()       : contraintes de types par relation (un Metric ne DELEGATES_TO personne).
#                               Un type inconnu (Unclassified) n'est JAMAIS pénalisé : schéma ouvert.
#   3. Policy / accept_*      : seuils de confiance, de support et de votes de la sortie finale.
#
# Les contraintes sont volontairement des INTERDICTIONS (liste noire de types) et non des listes
# blanches : une relation inhabituelle mais plausible passe, une relation absurde est pénalisée.

import re
from dataclasses import dataclass

from graph import vocabulary as V
from graph.schema import RELATION_TYPES, UNKNOWN_NODE_TYPE, UNKNOWN_RELATION_TYPE

# ---------------------------------------------------------------- entités
GENERIC_WORDS = frozenset("""
it its this that these those they them he she we you i the a an and or but if then which what who whom
there here example examples code note notes warning todo none null true false yes no etc other another
following above below section page docs documentation guide tutorial overview introduction summary
default value values name names type types data input output result results response responses request
requests error errors message messages string number object array list dict
""".split())

_URL = re.compile(r"://|^www\.|@[\w-]+\.[a-z]{2,}$", re.I)
_PATH_OR_FILE = re.compile(r"[\\/]|\.(?:py|js|ts|tsx|jsx|md|mdx|json|ya?ml|txt|csv|toml|ipynb|html|css|png|svg)$", re.I)
_VERSION = re.compile(r"^v?\d+(?:\.\d+){1,3}(?:[-+.\w]*)?$", re.I)
_ENV_VAR = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$|^[A-Z]{8,}$")
# identifiants internes de SDK : 4 "bosses" CamelCase ou plus (ResponseNewParamsInputUnion)
_SDK_IDENT = re.compile(r"^(?:[A-Z][a-z0-9]+){4,}$")


def is_valid_entity_name(name: str, known: bool | None = None) -> bool:
    """Un nom mérite-t-il un nœud ? `known` : nom du vocabulaire (jamais filtré par les heuristiques)."""
    n = (name or "").strip()
    if known is None:
        known = n in V.ENTITIES
    if known:
        return True
    if not (2 <= len(n) <= 60) or not re.search(r"[A-Za-z]", n):
        return False
    if len(n.split()) > 6 or n.lower() in GENERIC_WORDS:
        return False
    if _URL.search(n) or _PATH_OR_FILE.search(n) or _VERSION.match(n) or _ENV_VAR.match(n):
        return False
    if _SDK_IDENT.match(n):
        return False
    letters = sum(c.isalpha() for c in n)
    return letters / len(n) >= 0.6      # "x_1__", "a.b.c(d)" : trop de symboles


# ---------------------------------------------------------------- relations
_PASSIVE = {"Metric", "Dataset", "Language", "Artifact"}
# relation -> (types interdits en source, types interdits en cible)
FORBIDDEN = {
    "INVOKES":           (_PASSIVE | {"DataStore", "DataStructure"}, _PASSIVE | {"Task", "Concept", "DataStructure"}),
    "DELEGATES_TO":      (_PASSIVE | {"DataStore", "DataStructure", "Tool", "API"},
                          _PASSIVE | {"DataStore", "DataStructure", "Protocol", "API"}),
    "COLLABORATES_WITH": (_PASSIVE | {"DataStore", "DataStructure", "Tool", "API"},
                          _PASSIVE | {"DataStore", "DataStructure", "Tool", "API"}),
    "COMMUNICATES_WITH": (_PASSIVE | {"DataStructure"}, _PASSIVE | {"DataStructure"}),
    "ROUTES_TO":         (_PASSIVE | {"DataStore"}, _PASSIVE | {"DataStore"}),
    "TRIGGERS":          (_PASSIVE | {"DataStore", "DataStructure"}, _PASSIVE | {"DataStore", "DataStructure"}),
    "IMPLEMENTS":        ({"Metric", "Dataset", "Language"}, {"Metric", "Dataset", "Language", "Task"}),
    "STORES":            (_PASSIVE | {"Task"}, {"Language", "Framework", "Agent"}),
    "MEASURES":          ({"Language", "Dataset", "Artifact"}, set()),
    "EVALUATES":         ({"Language", "Dataset", "Artifact"}, set()),
    "INHERITS_FROM":     (_PASSIVE, _PASSIVE),
    "EXTENDS":           (_PASSIVE, _PASSIVE),
}
# relations de comparaison : les deux extrémités doivent appartenir à la même "famille"
_FAMILY = {"Framework": "software", "Platform": "software", "Tool": "software", "API": "software",
           "Protocol": "software", "Component": "software", "Agent": "software", "DataStore": "software",
           "DataStructure": "software", "Model": "model", "Language": "language",
           "Concept": "idea", "Technique": "idea", "Architecture": "idea", "Task": "idea",
           "Metric": "metric", "Dataset": "dataset", "Artifact": "artifact"}
SAME_FAMILY = {"ALTERNATIVE_TO", "SIMILAR_TO", "CONTRASTS_WITH"}
TYPE_VIOLATION_FACTOR = 0.5       # pénalité de confiance
RELATED_TO_FACTOR = 0.8           # RELATED_TO = prédicat inconnu : moins fiable par construction

assert all(r in RELATION_TYPES for r in list(FORBIDDEN) + list(SAME_FAMILY))


def check_relation(relation: str, source_type: str, target_type: str) -> tuple[bool, str]:
    """(ok, raison). Un type vide ou Unclassified ne viole jamais une contrainte."""
    st = source_type if source_type and source_type != UNKNOWN_NODE_TYPE else None
    tt = target_type if target_type and target_type != UNKNOWN_NODE_TYPE else None
    bad_src, bad_tgt = FORBIDDEN.get(relation, (set(), set()))
    if st in bad_src:
        return False, f"source {st} interdite pour {relation}"
    if tt in bad_tgt:
        return False, f"cible {tt} interdite pour {relation}"
    if relation in SAME_FAMILY and st and tt and _FAMILY.get(st) != _FAMILY.get(tt):
        return False, f"{st} et {tt} ne sont pas comparables ({relation})"
    return True, ""


# ---------------------------------------------------------------- politique de sortie
@dataclass
class Policy:
    min_entity_conf: float = 0.5
    min_relation_conf: float = 0.5
    related_to_min_conf: float = 0.7       # RELATED_TO doit être mieux établi qu'une relation typée
    unclassified_min_df: int = 2           # un type inconnu doit apparaître dans >= N chunks (ou 2 votes)
    drop_type_violations: bool = False     # False : pénalise seulement (confiance x 0.5)


def accept_entity(e: dict, p: Policy) -> bool:
    if not is_valid_entity_name(e["name"], known=e["name"] in V.ENTITIES):
        return False
    if e["confidence"] < p.min_entity_conf:
        return False
    if e["canonical_type"] == UNKNOWN_NODE_TYPE:
        return e.get("df", 1) >= p.unclassified_min_df or e.get("votes", 1) >= 2
    return True


def accept_relation(r: dict, p: Policy) -> bool:
    if not (r.get("evidence") or "").strip():
        return False                                   # SCHEMA_POLICY["require_evidence_for_relations"]
    if p.drop_type_violations and not r.get("type_ok", True):
        return False
    floor = p.related_to_min_conf if r["relation"] == UNKNOWN_RELATION_TYPE else p.min_relation_conf
    return r["confidence"] >= floor and r["source"] != r["target"]
