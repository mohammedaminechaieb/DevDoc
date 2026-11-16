# graph/resolution.py
# Owner: Aya
#
# RÉSOLUTION D'ENTITÉS à l'échelle du corpus (schéma : SCHEMA_POLICY["require_entity_resolution"]).
# Chaque extracteur renvoie des formes de surface ("state graph", "StateGraph", "Retrieval-Augmented
# Generation", "RAG"...). Sans résolution, le graphe est fragmenté : un même concept = plusieurs nœuds.
#
# Stratégie CONSERVATRICE (on préfère rater une fusion que fusionner deux concepts distincts) :
#   1. clé normalisée identique (casse, espaces, tirets, pluriel)           -> fusion sûre
#   2. acronyme : "Retrieval-Augmented Generation" ~ "RAG"                    -> fusion si non ambigu
#   3. quasi-doublons (fautes, variantes) : similarité >= fuzzy_threshold     -> fusion si types compatibles
#   Jamais fusionnés : deux entités du vocabulaire, ou deux noms qui ne diffèrent que par un nombre
#   (gpt4 / gpt3). Les cas douteux (similarité entre suggest_threshold et fuzzy_threshold, acronyme
#   ambigu, types incompatibles) sont écrits dans `suggestions` pour relecture humaine.
#
# Le nom canonique d'un cluster : nom du vocabulaire s'il existe, sinon la forme la plus fréquente.
# Le type : vote pondéré (confiance x occurrences, bonus dictionnaire) hors Unclassified.

import re
from collections import Counter, defaultdict
from typing import Iterable

from graph import vocabulary as V
from graph.normalize import canonical_entity_name, norm_key
from graph.schema import UNKNOWN_NODE_TYPE

try:                                            # rapidfuzz est optionnel (rapide) ; difflib en repli
    from rapidfuzz import fuzz

    def _ratio(a: str, b: str) -> float:
        return fuzz.ratio(a, b)
except ImportError:                             # pragma: no cover
    from difflib import SequenceMatcher

    def _ratio(a: str, b: str) -> float:
        return 100 * SequenceMatcher(None, a, b).ratio()

_SMALL_WORDS = {"of", "and", "the", "for", "a", "an", "in", "to", "with", "on"}


def acronym(name: str) -> str:
    """"Retrieval-Augmented Generation" -> "RAG" ; "" si moins de 2 mots significatifs."""
    words = [w for w in re.split(r"[^A-Za-z0-9]+", name) if w and w.lower() not in _SMALL_WORDS]
    return "".join(w[0] for w in words).upper() if len(words) >= 2 else ""


class _UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def _methods(e: dict) -> list[str]:
    m = e.get("method", [])
    return [m] if isinstance(m, str) else list(m)


class EntityResolver:
    def __init__(self, fuzzy_threshold: float = 94, suggest_threshold: float = 86, acronyms: bool = True):
        self.fuzzy_threshold, self.suggest_threshold, self.acronyms = fuzzy_threshold, suggest_threshold, acronyms
        self.clusters: dict[str, dict] = {}        # clé de cluster -> {key, name, canonical_type, ...}
        self.suggestions: list[dict] = []
        self._member: dict[str, str] = {}          # norm_key(forme) -> clé de cluster
        self._vocab_keys = {norm_key(n) for n in V.ENTITIES}

    # ------------------------------------------------------------------ apprentissage
    def fit(self, entities: Iterable[dict]) -> "EntityResolver":
        groups: dict[str, dict] = defaultdict(lambda: {"forms": Counter(), "types": Counter(), "raw": set(),
                                                       "methods": set(), "count": 0, "surfaces": set()})
        for e in entities:
            cname = canonical_entity_name(e["name"])      # alias / "the X" / "x()" résolus dès l'entrée
            k = norm_key(cname)
            if not k:
                continue
            g, w, ms = groups[k], max(int(e.get("count", 1)), 1), _methods(e)
            g["forms"][cname] += w
            g["surfaces"].add(e["name"].strip())          # formes d'origine : utiles comme alias de recherche
            g["count"] += w
            g["methods"].update(ms)
            if e.get("raw_type"):
                g["raw"].add(e["raw_type"])
            t = e.get("canonical_type", UNKNOWN_NODE_TYPE)
            if t != UNKNOWN_NODE_TYPE:
                g["types"][t] += w * float(e.get("confidence", 0.5)) * (1.5 if "dictionary" in ms else 1.0)

        keys = sorted(groups)
        uf = _UnionFind(keys)
        gtype = {k: (groups[k]["types"].most_common(1)[0][0] if groups[k]["types"] else UNKNOWN_NODE_TYPE) for k in keys}
        label = {k: groups[k]["forms"].most_common(1)[0][0] for k in keys}
        compat = lambda a, b: gtype[a] == gtype[b] or UNKNOWN_NODE_TYPE in (gtype[a], gtype[b])
        suggest = lambda a, b, score, reason: self.suggestions.append(
            {"a": label[a], "b": label[b], "score": round(score, 1), "reason": reason})

        if self.acronyms:
            by_acr: dict[str, list[str]] = defaultdict(list)
            for k in keys:
                a = acronym(label[k])
                if a and norm_key(a) in groups and norm_key(a) != k:
                    by_acr[norm_key(a)].append(k)
            for acr_key, longs in by_acr.items():
                if len(longs) == 1 and compat(longs[0], acr_key) and not self._both_vocab(longs[0], acr_key):
                    uf.union(longs[0], acr_key)
                else:
                    for lk in longs:
                        suggest(lk, acr_key, 100.0, "acronyme ambigu ou types incompatibles")

        buckets: dict[str, list[str]] = defaultdict(list)
        for k in keys:
            if len(k) >= 7:
                buckets[k[:3]].append(k)
        for bucket in buckets.values():
            for i, a in enumerate(bucket):
                for b in bucket[i + 1:]:
                    if abs(len(a) - len(b)) > 3 or re.findall(r"\d+", a) != re.findall(r"\d+", b):
                        continue
                    score = _ratio(a, b)
                    if score >= self.fuzzy_threshold and compat(a, b) and not self._both_vocab(a, b):
                        uf.union(a, b)
                    elif score >= self.suggest_threshold:
                        suggest(a, b, score, "quasi-doublon")

        members: dict[str, list[str]] = defaultdict(list)
        for k in keys:
            members[uf.find(k)].append(k)
        for ks in members.values():
            forms = Counter()
            types, raws, methods, count, surfaces = Counter(), set(), set(), 0, set()
            for k in ks:
                forms.update(groups[k]["forms"])
                surfaces |= groups[k]["surfaces"]
                types.update(groups[k]["types"])
                raws |= groups[k]["raw"]
                methods |= groups[k]["methods"]
                count += groups[k]["count"]
            vocab_form = next((f for f in forms if f in V.ENTITIES), None)
            name = vocab_form or max(forms, key=lambda f: (forms[f], f != f.lower(), -len(f)))
            name = canonical_entity_name(name)
            ckey = norm_key(name)
            self.clusters[ckey] = {
                "key": ckey, "name": name,
                "canonical_type": types.most_common(1)[0][0] if types else UNKNOWN_NODE_TYPE,
                "raw_types": sorted(raws),
                "aliases": sorted((set(forms) | surfaces) - {name}),
                "count": count, "methods": sorted(methods)}
            for k in ks:
                self._member[k] = ckey
        return self

    def _both_vocab(self, a: str, b: str) -> bool:
        return a in self._vocab_keys and b in self._vocab_keys

    # ------------------------------------------------------------------ utilisation
    def cluster_key(self, name: str) -> str:
        k = norm_key(canonical_entity_name(name))
        return self._member.get(k) or self._member.get(norm_key(name)) or k

    def canonical(self, name: str) -> str:
        c = self.clusters.get(self.cluster_key(name))
        return c["name"] if c else canonical_entity_name(name)

    def type_of(self, name: str) -> str:
        c = self.clusters.get(self.cluster_key(name))
        return c["canonical_type"] if c else UNKNOWN_NODE_TYPE
