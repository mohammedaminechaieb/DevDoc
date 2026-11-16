# scripts/evaluate_extractors.py
# Compare les extracteurs (et leurs combinaisons) au gold set : précision / rappel / F1,
# pour les entités, les relations (strict) et les paires (relation ignorée), + temps par chunk.
#
#   python -m scripts.evaluate_extractors --gold data/gold/gold.jsonl --extractors dictionary,gliner,relex,llm
#
# Seuls les chunks du gold set sont traités (donc peu de temps / peu d'appels LLM).
# Les sorties brutes sont sauvegardées dans data/eval/ pour ne pas tout relancer.

import argparse
import itertools
import json
import time
from pathlib import Path

import jsonlines

from config.settings import CORPUS_PATH, ROOT
from graph.evaluation import evaluate, load_jsonl
from graph.extractors import ALL_NAMES, get_extractor
from graph.merge import filter_by_votes, merge_extractions
from graph.normalize import CANDIDATES, write_candidates

ap = argparse.ArgumentParser()
ap.add_argument("--gold", default=str(ROOT / "data" / "gold" / "gold.jsonl"))
ap.add_argument("--extractors", default=",".join(ALL_NAMES))
ap.add_argument("--out-dir", default=str(ROOT / "data" / "eval"))
ap.add_argument("--reuse", action="store_true", help="réutilise les sorties déjà sauvegardées")
ap.add_argument("--no-llm-hints", action="store_true",
                help="LLM sans les entités candidates des extracteurs précédents (par défaut : mode guidé, "
                     "comme dans graph/pipeline.py)")
a = ap.parse_args()

out_dir = Path(a.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)
# une ligne non annotée (listes vides) est IGNORÉE, sauf si tu écris "noise": true (chunk volontairement vide)
rows_all = load_jsonl(a.gold)
gold = [g for g in rows_all if g["entities"] or g["relations"] or g.get("noise")]
print(f"{len(rows_all) - len(gold)} chunk(s) non annotés ignorés")
ids = {g["chunk_id"] for g in gold}
with jsonlines.open(CORPUS_PATH) as r:
    chunks = {c["chunk_id"]: c for c in r if c["chunk_id"] in ids}
print(f"gold: {len(gold)} chunks | entités: {sum(len(g['entities']) for g in gold)} "
      f"| relations: {sum(len(g['relations']) for g in gold)}")

outputs, timing = {}, {}
for name in a.extractors.split(","):
    cache = out_dir / f"outputs_{name}.json"
    if a.reuse and cache.exists():
        outputs[name] = json.loads(cache.read_text(encoding="utf-8"))
        continue
    try:
        ex = get_extractor(name)
        t0, res = time.time(), {}
        for cid, ch in chunks.items():
            if name == "llm" and not a.no_llm_hints:    # mode guidé : entités déjà trouvées par les autres
                hints = sorted({e["name"] for o in outputs.values() for e in o.get(cid, {}).get("entities", [])})
                res[cid] = ex.extract(ch, hints=hints)
            else:
                res[cid] = ex.extract(ch)
        timing[name] = (time.time() - t0) / max(len(chunks), 1)
        outputs[name] = res
        cache.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    except Exception as e:  # modèle non installé, clé API absente...
        print(f"[{name}] ignoré : {type(e).__name__}: {e}")

if not outputs:
    raise SystemExit("aucun extracteur n'a tourné")


def merged(names, votes=1):
    res = {cid: merge_extractions({n: outputs[n][cid] for n in names}) for cid in chunks}
    return {cid: filter_by_votes(x, votes) for cid, x in res.items()} if votes > 1 else res


rows = [(n, evaluate(o, gold), timing.get(n)) for n, o in outputs.items()]
names = list(outputs)
for k in range(2, len(names) + 1):
    for combo in itertools.combinations(names, k):
        rows.append(("+".join(combo) + " (union)", evaluate(merged(combo), gold), None))
        if k >= 3:
            rows.append(("+".join(combo) + " (vote>=2)", evaluate(merged(combo, 2), gold), None))

hdr = "| approche | ent. P | ent. R | ent. F1 | rel. P | rel. R | rel. F1 | paires F1 | s/chunk |\n|---|---|---|---|---|---|---|---|---|\n"
lines = []
for n, m, t in rows:
    e, r, p = m["entities"], m["relations"], m["pairs"]
    lines.append(f"| {n} | {e['precision']} | {e['recall']} | {e['f1']} | {r['precision']} | {r['recall']} | "
                 f"{r['f1']} | {p['f1']} | {'-' if t is None else round(t, 2)} |")
table = hdr + "\n".join(lines)
print("\n" + table)
(out_dir / "results.md").write_text(table, encoding="utf-8")
n = write_candidates(out_dir / "candidates.jsonl")
print(f"\n{n} types/prédicats inconnus à relire -> {out_dir / 'candidates.jsonl'}")
