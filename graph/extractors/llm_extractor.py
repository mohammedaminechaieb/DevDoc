# graph/extractors/llm_extractor.py - extracteur n°4 : LLM (entités + relations, sortie JSON validée)
#
# Le LLM est un simple callable complete(prompt) -> str : le fournisseur (Groq, Ollama...) est
# interchangeable. Pourquoi c'est l'extracteur le plus fiable pour les RELATIONS : il lit la phrase
# entière, choisit le prédicat du schéma et doit CITER la phrase source (evidence).
#
# Garde-fous (un LLM invente) :
#   - JSON validé par Pydantic ; sortie invalide -> un seul nouvel essai, jamais mise en cache
#   - entité absente du texte                          -> rejetée (anti-hallucination)
#   - relation sans evidence                           -> rejetée (SCHEMA_POLICY)
#   - evidence introuvable dans le chunk               -> rejetée (le LLM a reformulé / inventé)
#   - source ou cible absente de l'evidence            -> rejetée (pronom, coréférence, déduction)
#   - nom d'entité invalide (graph.validate)           -> rejeté
#   - cache disque par prompt : on ne repaie jamais un chunk déjà traité (reprise après coupure)
# Mode "guidé" : extract(chunk, hints=[noms]) injecte les entités déjà détectées (dictionnaire, GLiNER)
# dans le prompt : le LLM les réutilise telles quelles et se concentre sur les relations.

import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

from pydantic import BaseModel

from graph import vocabulary as V
from graph.entity_extractor import clean_text
from graph.extractors.base import make_entity, make_relation, windows
from graph.normalize import canonical_entity_name, norm_key
from graph.schema import NODE_TYPES, RELATION_TYPES, UNKNOWN_RELATION_TYPE
from graph.validate import is_valid_entity_name

PROMPT = """You build a knowledge graph from technical documentation about agentic AI (frameworks, protocols, LLM APIs).

ENTITY TYPES (use one of these; only if none fits, propose a short new type name):
<<TYPES>>

RELATION PREDICATES (use one of these; only if none fits, use a short verb phrase):
<<RELATIONS>>
<<CANDIDATES>>
RULES
1. Extract only what the text explicitly states. No outside knowledge, no guessing.
2. Entities are named things: frameworks, classes, functions, protocols, models, techniques, components. Write them as in the text. Never extract pronouns, generic words ("example", "code"), URLs, file paths, versions or environment variables.
3. A relation reads as a sentence: source PREDICATE target, e.g. "Agent USES Tool". The source performs, owns or depends; the target is the object.
4. "evidence" must be copied verbatim from the text and must contain BOTH the source and the target.
5. Skip marketing, vague, hypothetical or negated statements. Fewer correct relations beat many doubtful ones. If nothing qualifies, return empty lists.
6. Return ONLY JSON: {"entities":[{"name":"","type":""}],"relations":[{"source":"","predicate":"","target":"","evidence":""}]}

EXAMPLE
Text: "In LangGraph, a supervisor agent delegates subtasks to worker agents. The worker agents call external tools through MCP."
Output: {"entities":[{"name":"LangGraph","type":"Framework"},{"name":"supervisor agent","type":"Agent"},{"name":"worker agents","type":"Agent"},{"name":"MCP","type":"Protocol"}],"relations":[{"source":"supervisor agent","predicate":"DELEGATES_TO","target":"worker agents","evidence":"a supervisor agent delegates subtasks to worker agents"},{"source":"worker agents","predicate":"USES","target":"MCP","evidence":"The worker agents call external tools through MCP"}]}

TEXT (documentation of: <<FRAMEWORK>>)
\"\"\"
<<TEXT>>
\"\"\"
"""


class QuotaExceeded(RuntimeError):
    """Quota journalier du fournisseur atteint : inutile de réessayer, on reprend demain (--resume)."""


# ---------------------------------------------------------------- fournisseurs
class _Throttle:
    def __init__(self, rpm: float):
        self.interval, self.last = 60.0 / max(rpm, 1), 0.0

    def wait(self):
        delta = self.interval - (time.monotonic() - self.last)
        if delta > 0:
            time.sleep(delta)
        self.last = time.monotonic()


_throttle = _Throttle(float(os.getenv("LLM_RPM", "25")))       # palier gratuit Groq : 30 requêtes/min


def _retrying(fn: Callable[[], str], retries: int = 5) -> str:
    for attempt in range(retries + 1):
        _throttle.wait()
        try:
            return fn()
        except Exception as e:                                  # noqa: BLE001 - classé par message
            msg = str(e).lower()
            if "per day" in msg or "tpd" in msg or "daily" in msg:
                raise QuotaExceeded(str(e)) from e
            transient = any(t in msg for t in ("429", "rate limit", "timeout", "timed out", "502", "503",
                                               "overloaded", "connection"))
            if not transient or attempt == retries:
                raise
            m = re.search(r"try again in ([\d.]+)\s*(ms|s)", msg)
            pause = (float(m.group(1)) / (1000 if m.group(2) == "ms" else 1) + 0.5) if m else min(60, 2 ** attempt * 2)
            time.sleep(pause)
    raise RuntimeError("unreachable")


def _model_name() -> str:
    from config.settings import LLM_MODEL
    return os.getenv("GRAPH_LLM_MODEL") or LLM_MODEL        # modèle d'extraction distinct de celui de génération


def groq_complete(prompt: str) -> str:
    from groq import Groq
    from config.settings import GROQ_API_KEY
    client = Groq(api_key=GROQ_API_KEY, max_retries=0)       # les reprises sont gérées par _retrying
    return _retrying(lambda: client.chat.completions.create(
        model=_model_name(), temperature=0, response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}]).choices[0].message.content)


def ollama_complete(prompt: str) -> str:
    import httpx
    from config.settings import OLLAMA_URL

    def call() -> str:
        r = httpx.post(f"{OLLAMA_URL}/api/chat", timeout=180, json={
            "model": _model_name(), "stream": False, "format": "json", "options": {"temperature": 0},
            "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        return r.json()["message"]["content"]
    return _retrying(call)


def default_complete(prompt: str) -> str:
    """Fournisseur choisi par config/settings.py (LLM_PROVIDER = groq | ollama)."""
    from config.settings import LLM_PROVIDER
    if LLM_PROVIDER == "ollama":
        return ollama_complete(prompt)
    return groq_complete(prompt)


# ---------------------------------------------------------------- validation
class _Ent(BaseModel):
    name: str
    type: str = ""


class _Rel(BaseModel):
    source: str
    predicate: str
    target: str
    evidence: str = ""


class _Out(BaseModel):
    entities: list[_Ent] = []
    relations: list[_Rel] = []


def parse_json(raw: str) -> dict:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        s = s[4:] if s.lower().startswith("json") else s
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        a, b = s.find("{"), s.rfind("}")
        return json.loads(s[a:b + 1]) if a >= 0 and b > a else {}


def _flat(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


_ALIASES_OF = defaultdict(set)                       # nom canonique -> formes de surface connues
for _alias, _canon in V.ALIASES.items():
    _ALIASES_OF[_canon].add(_flat(_alias))


def _surface_forms(name: str) -> set[str]:
    canon = canonical_entity_name(name)
    forms = {_flat(name), _flat(canon)} | _ALIASES_OF.get(canon, set())
    return {f for f in forms if f} | {f[:-1] for f in forms if len(f) > 3 and f.endswith("s")}


def occurs_in(name: str, flat_text: str) -> bool:
    return any(f in flat_text for f in _surface_forms(name))


def evidence_in_text(evidence: str, text: str) -> bool:
    """La citation existe-t-elle dans le chunk ? Contiguë (ponctuation ignorée) ou, à défaut, >= 90 %
    de ses mots présents dans le chunk (le LLM peut omettre un mot ou un signe)."""
    e, t = _flat(evidence), _flat(text)
    if len(e) < 12:
        return False
    if e in t:
        return True
    words = re.findall(r"[a-z0-9]+", evidence.lower())
    pool = set(re.findall(r"[a-z0-9]+", text.lower()))
    return len(words) >= 5 and sum(w in pool for w in words) / len(words) >= 0.9


class _Cache:
    def __init__(self, path):
        self.path, self.data = (Path(path) if path else None), {}
        if self.path and self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.data[row["k"]] = row["v"]

    def get(self, k):
        return self.data.get(k)

    def set(self, k, v):
        self.data[k] = v
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"k": k, "v": v}, ensure_ascii=False) + "\n")


class LLMExtractor:
    name = "llm"

    def __init__(self, complete: Callable[[str], str] | None = None,
                 cache_path="data/cache/llm_extractions.jsonl", max_chars=4000, confidence=0.7,
                 max_windows=3, max_entities=30, max_relations=25):
        self.complete, self.max_chars, self.confidence = complete or default_complete, max_chars, confidence
        self.max_windows, self.max_entities, self.max_relations = max_windows, max_entities, max_relations
        if isinstance(cache_path, str) and not os.path.isabs(cache_path):
            cache_path = Path(__file__).resolve().parents[2] / cache_path   # relatif à la racine du dépôt
        self.cache = _Cache(cache_path)
        self.stats = Counter()          # calls, cache_hits, parse_errors, rejected_* : rapporté dans le manifest

    # -- prompt
    def _prompt(self, chunk: dict, text: str, hints: list[str]) -> str:
        flat = _flat(text)
        local = [h for h in hints if occurs_in(h, flat)][:40]
        cand = ("\nCANDIDATE ENTITIES already detected in this text (reuse these exact names when they apply; "
                "add others only if clearly named in the text):\n" + ", ".join(local) + "\n") if local else ""
        return (PROMPT.replace("<<TYPES>>", "\n".join(f"- {k}: {v}" for k, v in NODE_TYPES.items()))
                .replace("<<RELATIONS>>", ", ".join(r for r in RELATION_TYPES if r != UNKNOWN_RELATION_TYPE))
                .replace("<<CANDIDATES>>", cand)
                .replace("<<FRAMEWORK>>", chunk.get("framework", "unknown"))
                .replace("<<TEXT>>", text))

    # -- appel + cache
    def _ask(self, prompt: str) -> _Out | None:
        key = hashlib.sha1(prompt.encode()).hexdigest()
        raw = self.cache.get(key)
        if raw is not None:
            self.stats["cache_hits"] += 1
            return _Out.model_validate(parse_json(raw))
        for attempt in range(2):                                  # un seul nouvel essai
            self.stats["calls"] += 1
            raw = self.complete(prompt if attempt == 0 else
                                prompt + "\n\nYour previous answer was not valid JSON. Return ONLY the JSON object.")
            try:
                out = _Out.model_validate(parse_json(raw))
            except Exception:                                      # noqa: BLE001 - JSON ou schéma invalide
                self.stats["parse_errors"] += 1
                continue
            self.cache.set(key, raw)                               # seules les sorties valides sont cachées
            return out
        return None

    # -- extraction
    def extract(self, chunk: dict, hints: list[str] | None = None) -> dict:
        text = clean_text(chunk.get("text", ""))
        hints = hints or []
        hint_flat = {_flat(h) for h in hints}
        ents, rels = {}, {}
        for _, window in windows(text, self.max_chars)[: self.max_windows]:
            out = self._ask(self._prompt(chunk, window, hints))
            if out is None:
                continue
            flat_w = _flat(window)
            for e in out.entities[: self.max_entities]:
                if not (is_valid_entity_name(e.name) and occurs_in(e.name, flat_w)):   # anti-hallucination
                    self.stats["rejected_entity"] += 1
                    continue
                ents[norm_key(canonical_entity_name(e.name))] = make_entity(e.name, e.type, chunk, "llm", self.confidence)
            for r in out.relations[: self.max_relations]:
                ev, ev_flat = r.evidence.strip(), _flat(r.evidence)
                if not ev:
                    self.stats["rejected_no_evidence"] += 1
                elif not evidence_in_text(ev, window):
                    self.stats["rejected_evidence_not_in_text"] += 1
                elif not (occurs_in(r.source, ev_flat) and occurs_in(r.target, ev_flat)):
                    self.stats["rejected_endpoint_not_in_evidence"] += 1
                elif not (is_valid_entity_name(r.source) and is_valid_entity_name(r.target)):
                    self.stats["rejected_entity"] += 1
                else:
                    rel = make_relation(r.source, r.target, r.predicate, chunk, "llm", self.confidence, ev)
                    if rel["source"] == rel["target"]:
                        continue
                    c = self.confidence - (0.15 if rel["relation"] == UNKNOWN_RELATION_TYPE else 0.0)
                    if _flat(r.source) in hint_flat and _flat(r.target) in hint_flat:
                        c += 0.1                                       # extrémités déjà confirmées par un autre extracteur
                    rel["confidence"] = round(min(c, 0.95), 3)
                    for end in (r.source, r.target):                   # une relation a toujours ses deux nœuds
                        ents.setdefault(norm_key(canonical_entity_name(end)),
                                        make_entity(end, "", chunk, "llm", self.confidence))
                    rels[(norm_key(rel["source"]), rel["relation"], norm_key(rel["target"]))] = rel
        return {"entities": list(ents.values()), "relations": list(rels.values())}
