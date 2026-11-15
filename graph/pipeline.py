# graph/pipeline.py
# Owner: Aya
#
# PIPELINE D'EXTRACTION DU GRAPHE (hors ligne, reprenable). Produit data/graph/*.jsonl, que
# graph/neo4j_loader.py charge ensuite dans Neo4j.
#
#   python -m graph.pipeline                          # profil "quality" : dictionnaire + GLiNER + LLM guidé
#   python -m graph.pipeline --profile standard       # sans LLM (gratuit, local)
#   python -m graph.pipeline --llm-max-chunks 300     # budget LLM (quota journalier) ; relancer = reprise
#   python -m graph.pipeline --estimate               # nombre de chunks éligibles + coût LLM estimé
#
# Approche (cascade hybride, du moins cher au plus précis) :
#   0. tri      : graph.preprocess  -> CSS / boilerplate ignorés ; code / changelog : dictionnaire seul
#   1. ancres   : dictionnaire (vocabulaire + règles)                   - tous les chunks utiles
#   2. rappel   : GLiNER (NER zero-shot sur les 18 types du schéma)     - chunks informatifs
#   3. relations: LLM GUIDÉ par les entités des étapes 1-2, evidence vérifiée dans le texte
#                 - chunks informatifs avec >= 2 entités candidates, par ordre de densité (budget)
#   4. fusion   : graph.merge (accord entre méthodes = confiance), par chunk
#   5. résolution d'entités sur tout le corpus : graph.resolution
#   6. validation : contraintes de types (graph.validate), seuils, evidence obligatoire
#   7. agrégation : un nœud par entité, une arête par (source, RELATION, cible) avec sa provenance
#
# Les sorties brutes de chaque extracteur sont écrites au fil de l'eau dans data/graph/raw/<nom>.jsonl :
# une coupure (quota, Ctrl+C) ne fait rien perdre, et la relance reprend où elle s'était arrêtée.

import argparse
import json
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import jsonlines

from graph import vocabulary as V
from graph.extractors import get_extractor
from graph.merge import merge_extractions
from graph.preprocess import profile_chunk
from graph.resolution import EntityResolver
from graph.schema import UNKNOWN_NODE_TYPE, UNKNOWN_RELATION_TYPE
from graph.validate import (RELATED_TO_FACTOR, TYPE_VIOLATION_FACTOR, Policy, accept_entity,
                            accept_relation, check_relation)

PROFILES = {
    "fast":     ["dictionary"],
    "standard": ["dictionary", "gliner"],
    "quality":  ["dictionary", "gliner", "llm"],
    "max":      ["dictionary", "gliner", "relex", "llm"],
}
MODEL_EXTRACTORS = {"gliner", "relex", "llm"}      # réservés aux chunks "informatifs"
MAX_CONSECUTIVE_ERRORS = 5                          # disjoncteur : extracteur désactivé après N échecs d'affilée
MAX_CHUNK_IDS = 50                                  # provenance stockée par arête (les plus sûres d'abord)

try:
    from tqdm import tqdm
except ImportError:                                 # pragma: no cover
    def tqdm(it, **_):
        return it


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _log(msg: str, verbose: bool = True):
    if verbose:
        print(msg, flush=True)


# ------------------------------------------------------------------ stockage reprenable
class RawStore:
    """Résultats bruts d'UN extracteur, un JSON par ligne : {"chunk_id", "result"}. Append-only."""

    def __init__(self, path: Path):
        self.path, self.data = path, {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.data[row["chunk_id"]] = row["result"]

    def __contains__(self, cid):
        return cid in self.data

    def get(self, cid):
        return self.data.get(cid)

    def put(self, cid, result):
        self.data[cid] = result
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"chunk_id": cid, "result": result}, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------ corpus
def load_corpus(path, limit=None, frameworks=None) -> list[dict]:
    keep = set(frameworks) if frameworks else None
    out = []
    with jsonlines.open(path) as reader:
        for ch in reader:
            if keep is None or ch.get("framework") in keep:
                out.append(ch)
                if limit and len(out) >= limit:
                    break
    return out


def _availability(name: str) -> str | None:
    """None si l'extracteur peut tourner, sinon la raison (dépendance absente, clé API manquante)."""
    if name in ("gliner", "relex"):
        try:
            import gliner  # noqa: F401
        except ImportError:
            return "paquet `gliner` non installé (pip install -r graph/requirements-extraction.txt)"
    if name == "llm":
        from config.settings import GROQ_API_KEY, LLM_PROVIDER
        if LLM_PROVIDER == "groq":
            try:
                import groq  # noqa: F401
            except ImportError:
                return "paquet `groq` non installé"
            if not GROQ_API_KEY or GROQ_API_KEY.startswith("your_"):
                return "GROQ_API_KEY absente de config/.env"
    return None


def _entity_names(result: dict | None) -> list[str]:
    return [e["name"] for e in (result or {}).get("entities", [])]


# ------------------------------------------------------------------ étapes 1-3 : extraction
def _run_one(ex, chunk, state, name, verbose, **kw):
    try:
        res = ex.extract(chunk, **kw)
        state["errors_in_a_row"][name] = 0
        return res
    except Exception as e:                                  # noqa: BLE001 - un chunk ne doit pas tout arrêter
        from graph.extractors.llm_extractor import QuotaExceeded
        if isinstance(e, QuotaExceeded):
            raise
        state["errors"][name] += 1
        state["errors_in_a_row"][name] += 1
        if state["errors"][name] <= 3:
            _log(f"  [{name}] erreur sur {chunk['chunk_id']}: {type(e).__name__}: {str(e)[:200]}", verbose)
        if state["errors_in_a_row"][name] >= MAX_CONSECUTIVE_ERRORS:
            state["disabled"][name] = f"{MAX_CONSECUTIVE_ERRORS} erreurs consécutives ({type(e).__name__}: {str(e)[:120]})"
        return None


def extract_all(chunks, profiles, extractors: dict, stores: dict, llm_max_chunks=None, llm_min_entities=2,
                verbose=True) -> dict:
    state = {"errors": Counter(), "errors_in_a_row": Counter(), "disabled": {}, "done": Counter(),
             "llm_eligible": 0, "llm_selected": 0, "stopped": None}
    stage1 = {n: ex for n, ex in extractors.items() if n != "llm"}

    for ch in tqdm(chunks, desc="dictionnaire + modèles NER", disable=not verbose):
        cid, prof = ch["chunk_id"], profiles[ch["chunk_id"]]
        if prof["skip_all"]:
            continue
        for name, ex in stage1.items():
            if name in state["disabled"] or cid in stores[name]:
                continue
            if name in MODEL_EXTRACTORS and not prof["informative"]:
                continue
            res = _run_one(ex, ch, state, name, verbose)
            if res is not None:
                stores[name].put(cid, res)
                state["done"][name] += 1

    llm = extractors.get("llm")
    if llm is None:
        return state
    hints_of = {}
    for ch in chunks:
        cid = ch["chunk_id"]
        if not profiles[cid]["informative"]:
            continue
        names = {n for s in stage1 for n in _entity_names(stores[s].get(cid))}
        if len(names) >= llm_min_entities:
            hints_of[cid] = sorted(names)
    state["llm_eligible"] = len(hints_of)
    todo = [ch for ch in chunks if ch["chunk_id"] in hints_of and ch["chunk_id"] not in stores["llm"]]
    # priorité : les chunks les plus denses en entités (là où sont les relations), puis les mieux notés
    todo.sort(key=lambda c: (-len(hints_of[c["chunk_id"]]), -float(c.get("quality_score") or 0)))
    if llm_max_chunks is not None:
        todo = todo[:llm_max_chunks]
    state["llm_selected"] = len(todo)
    _log(f"LLM : {len(hints_of)} chunks éligibles, {len(stores['llm'].data)} déjà faits, {len(todo)} à traiter", verbose)
    from graph.extractors.llm_extractor import QuotaExceeded
    try:
        for ch in tqdm(todo, desc="LLM guidé", disable=not verbose):
            if "llm" in state["disabled"]:
                break
            res = _run_one(llm, ch, state, "llm", verbose, hints=hints_of[ch["chunk_id"]])
            if res is not None:
                stores["llm"].put(ch["chunk_id"], res)
                state["done"]["llm"] += 1
    except QuotaExceeded as e:
        state["stopped"] = f"quota LLM atteint : {str(e)[:200]} -> relancer plus tard (la reprise est automatique)"
        _log(state["stopped"], verbose)
    except KeyboardInterrupt:
        state["stopped"] = "interrompu par l'utilisateur -> relancer pour reprendre"
        _log(state["stopped"], verbose)
    return state


# ------------------------------------------------------------------ étapes 4-7 : assemblage
def _noisy_or(values):
    p = 1.0
    for v in values:
        p *= 1 - v
    return 1 - p


def _as_list(x):
    return [x] if isinstance(x, str) else list(x or [])


def assemble(chunks, stores: dict, policy: Policy | None = None, resolver: EntityResolver | None = None) -> dict:
    policy = policy or Policy()
    meta = {c["chunk_id"]: c for c in chunks}

    # 4. fusion par chunk
    per_chunk = {}
    for cid in meta:
        named = {n: s.get(cid) for n, s in stores.items() if cid in s}
        if named:
            per_chunk[cid] = merge_extractions(named)

    # 5. résolution d'entités (les extrémités de relations comptent aussi comme mentions)
    def mentions_of(m):
        yield from m["entities"]
        for r in m["relations"]:
            for end, t in ((r["source"], r.get("source_type")), (r["target"], r.get("target_type"))):
                yield {"name": end, "canonical_type": t or UNKNOWN_NODE_TYPE, "count": 1,
                       "confidence": r["confidence"], "method": r["extraction_method"]}

    resolver = (resolver or EntityResolver()).fit(e for m in per_chunk.values() for e in mentions_of(m))
    clusters = resolver.clusters

    ents = {}
    mentions = {}
    candidates = {"node_type": Counter(), "relation": Counter()}

    def touch(key, cid, count, conf, methods, votes=1):
        c = clusters[key]
        e = ents.setdefault(key, {**{k: c[k] for k in ("key", "name", "canonical_type", "raw_types", "aliases")},
                                  "description": None, "count": 0, "df": set(), "confidence": 0.0, "votes": 1,
                                  "methods": set(), "frameworks": set(), "source_documents": set()})
        e["count"] += count
        e["df"].add(cid)
        e["confidence"] = max(e["confidence"], conf)
        e["votes"] = max(e["votes"], votes)
        e["methods"] |= set(methods)
        e["frameworks"].add(meta[cid].get("framework"))
        e["source_documents"].add(meta[cid].get("source_id") or cid)
        m = mentions.setdefault((key, cid), {"entity_key": key, "chunk_id": cid, "count": 0,
                                             "confidence": 0.0, "methods": set()})
        m["count"] += count
        m["confidence"] = max(m["confidence"], conf)
        m["methods"] |= set(methods)

    for cid, m in per_chunk.items():
        for e in m["entities"]:
            key = resolver.cluster_key(e["name"])
            if key in clusters:
                touch(key, cid, max(int(e.get("count", 1)), 1), float(e["confidence"]),
                      _as_list(e["method"]), e.get("votes", 1))
                if e["canonical_type"] == UNKNOWN_NODE_TYPE and e.get("raw_type"):
                    candidates["node_type"][e["raw_type"].lower()] += 1

    # 6-7. relations : résolution des extrémités, contraintes de types, agrégation
    support = defaultdict(list)
    for cid, m in per_chunk.items():
        for r in m["relations"]:
            sk, tk = resolver.cluster_key(r["source"]), resolver.cluster_key(r["target"])
            if sk == tk or sk not in clusters or tk not in clusters:
                continue
            for k in (sk, tk):                       # l'extrémité est bien mentionnée dans ce chunk
                if (k, cid) not in mentions:
                    touch(k, cid, 1, float(r["confidence"]), _as_list(r["extraction_method"]))
            rel = r["relation"]
            ok, why = check_relation(rel, clusters[sk]["canonical_type"], clusters[tk]["canonical_type"])
            conf = float(r["confidence"]) * (1 if ok else TYPE_VIOLATION_FACTOR)
            if rel == UNKNOWN_RELATION_TYPE:
                conf *= RELATED_TO_FACTOR
                if r.get("raw_predicate"):
                    candidates["relation"][r["raw_predicate"].lower()] += 1
            support[(sk, rel, tk)].append({**r, "confidence": conf, "chunk_id": cid, "type_ok": ok, "type_issue": why})

    relations = []
    for (sk, rel, tk), rows in support.items():
        rows.sort(key=lambda x: (-x["confidence"], -len(x.get("evidence") or "")))
        best = rows[0]
        by_chunk = {}
        for x in rows:                                # une voix par chunk (pas de double comptage)
            by_chunk[x["chunk_id"]] = max(by_chunk.get(x["chunk_id"], 0), x["confidence"])
        relations.append({
            "source": clusters[sk]["name"], "target": clusters[tk]["name"], "source_key": sk, "target_key": tk,
            "relation": rel, "raw_predicate": best.get("raw_predicate"),
            "raw_predicates": sorted({x.get("raw_predicate") for x in rows if x.get("raw_predicate")}),
            "confidence": round(min(_noisy_or(by_chunk.values()), 0.99), 3), "support": len(by_chunk),
            "evidence": best.get("evidence", ""), "source_chunk_id": best["chunk_id"],
            "source_url": best.get("source_url"), "document_version": best.get("document_version"),
            "extraction_method": sorted({m for x in rows for m in _as_list(x["extraction_method"])}),
            "chunk_ids": list(dict.fromkeys(x["chunk_id"] for x in rows))[:MAX_CHUNK_IDS],
            "type_ok": best["type_ok"], "type_issue": best["type_issue"] or None})

    # politique de sortie
    entities = []
    for e in ents.values():
        e = {**e, "df": len(e["df"]), "confidence": round(e["confidence"], 3),
             **{k: sorted(x for x in e[k] if x) for k in ("methods", "frameworks", "source_documents")}}
        if accept_entity(e, policy):
            entities.append(e)
    kept = {e["key"] for e in entities}
    relations = [r for r in relations if r["source_key"] in kept and r["target_key"] in kept and accept_relation(r, policy)]
    ment = [{**m, "confidence": round(m["confidence"], 3), "methods": sorted(m["methods"])}
            for m in mentions.values() if m["entity_key"] in kept]

    entities.sort(key=lambda e: (-e["df"], e["name"]))
    relations.sort(key=lambda r: (-r["confidence"], -r["support"], r["source"]))
    return {"entities": entities, "relations": relations, "mentions": ment,
            "suggestions": resolver.suggestions, "candidates": candidates,
            "dropped": {"entities": len(ents) - len(entities), "relations": len(support) - len(relations)}}


# ------------------------------------------------------------------ export
def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def export(graph: dict, out_dir: Path, manifest: dict):
    _write_jsonl(out_dir / "entities.jsonl", graph["entities"])
    _write_jsonl(out_dir / "relations.jsonl", graph["relations"])
    _write_jsonl(out_dir / "mentions.jsonl", graph["mentions"])
    # à relire à la main : fusions douteuses, types/prédicats hors schéma, termes à ajouter au vocabulaire
    _write_jsonl(out_dir / "review" / "merge_suggestions.jsonl", graph["suggestions"])
    _write_jsonl(out_dir / "review" / "candidates.jsonl",
                 [{"kind": k, "raw": raw, "count": c} for k, ctr in graph["candidates"].items()
                  for raw, c in ctr.most_common()])
    _write_jsonl(out_dir / "review" / "vocabulary_suggestions.jsonl",
                 [{"name": e["name"], "type": e["canonical_type"], "df": e["df"], "frameworks": e["frameworks"],
                   "methods": e["methods"]} for e in graph["entities"]
                  if e["name"] not in V.ENTITIES and e["df"] >= 5 and e["canonical_type"] != UNKNOWN_NODE_TYPE])
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


# ------------------------------------------------------------------ orchestration
def run(corpus_path=None, out_dir=None, profile="quality", extractors=None, limit=None, frameworks=None,
        llm_max_chunks=None, llm_min_entities=2, policy: Policy | None = None, strict=False, fresh=False,
        verbose=True) -> dict:
    """extractors : None (profil), liste de noms, ou dict {nom: instance} (tests, modèles déjà chargés)."""
    from config.settings import CORPUS_PATH
    corpus_path = corpus_path or CORPUS_PATH
    out_dir = Path(out_dir or _root() / "data" / "graph")
    policy = policy or Policy()
    t0 = time.time()

    chunks = load_corpus(corpus_path, limit, frameworks)
    profiles = {c["chunk_id"]: profile_chunk(c) for c in chunks}
    kinds = Counter(p["kind"] for p in profiles.values())
    _log(f"{len(chunks)} chunks | {dict(kinds)}", verbose)

    skipped = {}
    if isinstance(extractors, dict):
        instances = dict(extractors)
    else:
        names = list(extractors or PROFILES[profile])
        instances = {}
        for n in names:
            why = _availability(n)
            if why:
                if strict:
                    raise SystemExit(f"[{n}] indisponible : {why}")
                skipped[n] = why
                _log(f"[{n}] IGNORÉ : {why}", verbose)
                continue
            instances[n] = get_extractor(n)

    raw_dir = out_dir / "raw"
    if fresh:
        for n in instances:
            (raw_dir / f"{n}.jsonl").unlink(missing_ok=True)
    stores = {n: RawStore(raw_dir / f"{n}.jsonl") for n in instances}
    state = extract_all(chunks, profiles, instances, stores, llm_max_chunks, llm_min_entities, verbose)
    for n, why in state["disabled"].items():
        skipped[n] = why
        _log(f"[{n}] DÉSACTIVÉ en cours de route : {why}", verbose)

    graph = assemble(chunks, stores, policy)
    rels_by_type = Counter(r["relation"] for r in graph["relations"])
    llm_stats = dict(getattr(instances.get("llm"), "stats", {}) or {})
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "corpus": str(corpus_path), "profile": profile if not isinstance(extractors, dict) else "custom",
        "extractors_used": sorted(instances), "extractors_skipped": skipped,
        "chunks": len(chunks), "chunk_kinds": dict(kinds),
        "processed": {n: len(s.data) for n, s in stores.items()},
        "llm": {"eligible": state["llm_eligible"], "selected_this_run": state["llm_selected"],
                "done_total": len(stores["llm"].data) if "llm" in stores else 0, **llm_stats},
        "errors": dict(state["errors"]), "incomplete": state["stopped"],
        "policy": asdict(policy),
        "counts": {"entities": len(graph["entities"]), "relations": len(graph["relations"]),
                   "mentions": len(graph["mentions"]), "dropped": graph["dropped"],
                   "entities_by_type": dict(Counter(e["canonical_type"] for e in graph["entities"])),
                   "relations_by_type": dict(rels_by_type)},
        "seconds": round(time.time() - t0, 1)}
    export(graph, out_dir, manifest)
    _log(f"\n{manifest['counts']['entities']} entités | {manifest['counts']['relations']} relations | "
         f"{manifest['counts']['mentions']} mentions -> {out_dir}", verbose)
    _log(f"relations : {dict(rels_by_type.most_common())}", verbose)
    if skipped or state["stopped"]:
        _log("ATTENTION : extraction partielle, voir manifest.json (extractors_skipped / incomplete)", verbose)
    return manifest


def estimate(corpus_path=None, limit=None, min_entities=2, tokens_per_day=500_000):
    """Combien de chunks iraient au LLM, et combien de tokens ? (borne basse : candidats du dictionnaire seul)"""
    from config.settings import CORPUS_PATH
    from graph.extractors.llm_extractor import LLMExtractor
    chunks = load_corpus(corpus_path or CORPUS_PATH, limit)
    dico, llm = get_extractor("dictionary"), LLMExtractor(complete=lambda p: "{}", cache_path=None)
    base = len(llm._prompt({"framework": "x"}, "", [])) / 4
    eligible = [c for c in chunks if profile_chunk(c)["informative"]
                and len(dico.extract(c)["entities"]) >= min_entities]
    tokens = sum(base + min(len(c["text"]), 4000) / 4 + 60 + 300 for c in eligible)   # prompt + texte + candidats + sortie
    print(f"{len(eligible)} / {len(chunks)} chunks éligibles au LLM (>= {min_entities} entités du dictionnaire)")
    print(f"~{tokens / 1e6:.2f} M tokens (~{tokens / max(len(eligible), 1):.0f} par chunk) "
          f"-> ~{tokens / tokens_per_day:.1f} jour(s) à {tokens_per_day:,} tokens/jour")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extraction du knowledge graph -> data/graph/")
    ap.add_argument("--profile", choices=sorted(PROFILES), default="quality")
    ap.add_argument("--extractors", help="liste explicite, ex. dictionary,gliner (remplace --profile)")
    ap.add_argument("--corpus")
    ap.add_argument("--out", help="dossier de sortie (défaut : data/graph)")
    ap.add_argument("--limit", type=int, help="n premiers chunks seulement (tests)")
    ap.add_argument("--frameworks", help="ex. langgraph,mcp")
    ap.add_argument("--llm-max-chunks", type=int, help="budget LLM de ce lancement (reprise au suivant)")
    ap.add_argument("--llm-min-entities", type=int, default=2)
    ap.add_argument("--min-entity-conf", type=float, default=Policy.min_entity_conf)
    ap.add_argument("--min-relation-conf", type=float, default=Policy.min_relation_conf)
    ap.add_argument("--drop-type-violations", action="store_true")
    ap.add_argument("--strict", action="store_true", help="échoue si un extracteur demandé est indisponible")
    ap.add_argument("--fresh", action="store_true", help="ignore les sorties brutes déjà calculées")
    ap.add_argument("--estimate", action="store_true", help="estime le coût LLM puis s'arrête")
    a = ap.parse_args(argv)
    if a.estimate:
        return estimate(a.corpus, a.limit, a.llm_min_entities)
    run(corpus_path=a.corpus, out_dir=a.out, profile=a.profile,
        extractors=a.extractors.split(",") if a.extractors else None, limit=a.limit,
        frameworks=a.frameworks.split(",") if a.frameworks else None, llm_max_chunks=a.llm_max_chunks,
        llm_min_entities=a.llm_min_entities, strict=a.strict, fresh=a.fresh,
        policy=Policy(min_entity_conf=a.min_entity_conf, min_relation_conf=a.min_relation_conf,
                      drop_type_violations=a.drop_type_violations))


if __name__ == "__main__":
    main()
