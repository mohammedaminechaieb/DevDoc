# scripts/make_gold_sample.py
# Tire un échantillon STRATIFIÉ (autant que possible le même nombre de chunks par framework)
# à annoter à la main -> c'est le jeu de référence (gold set) de la comparaison d'extracteurs.
#
#   python -m scripts.make_gold_sample --n 80
#   -> data/gold/to_annotate.jsonl  (à copier en data/gold/gold.jsonl puis à remplir)
#
# CONSIGNES D'ANNOTATION
#  * Annote AVANT de regarder la sortie d'un modèle (sinon tu seras influencée).
#  * "entities"  : tout ce qui mérite un nœud : [{"name": "StateGraph", "type": "Component"}]
#  * "relations" : seulement ce que le TEXTE affirme : [{"source": "Agent", "relation": "USES", "target": "Tool"}]
#    (relation = un type de graph/schema.py RELATION_TYPES ; si aucun ne convient : "RELATED_TO")
#  * Ne déduis rien de ta connaissance du framework : si ce n'est pas écrit dans le chunk, ce n'est pas gold.
#  * Chunk du bruit (changelog, navigation...) : mets "noise": true à la racine de la ligne (listes vides).
#    Une ligne laissée vide SANS "noise": true est considérée comme non annotée et ignorée.

import argparse
import collections
import json
import random
from pathlib import Path

import jsonlines

from config.settings import CORPUS_PATH, ROOT
from graph.entity_extractor import clean_text

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=80)
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--min-chars", type=int, default=300, help="ignore les chunks trop courts")
ap.add_argument("--max-chars", type=int, default=1500, help="ignore les chunks trop longs à annoter")
ap.add_argument("--out", default=str(ROOT / "data" / "gold" / "to_annotate.jsonl"))
a = ap.parse_args()

by_fw = collections.defaultdict(list)
with jsonlines.open(CORPUS_PATH) as r:
    for ch in r:
        if a.min_chars <= len(clean_text(ch["text"])) <= a.max_chars:
            by_fw[ch["framework"]].append(ch)

rng = random.Random(a.seed)
for lst in by_fw.values():
    rng.shuffle(lst)
picked, fws = [], sorted(by_fw)
while len(picked) < a.n and any(by_fw[f] for f in fws):   # tourniquet entre frameworks
    for f in fws:
        if by_fw[f] and len(picked) < a.n:
            picked.append(by_fw[f].pop())

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
with open(a.out, "w", encoding="utf-8") as f:
    for ch in picked:
        f.write(json.dumps({"chunk_id": ch["chunk_id"], "framework": ch["framework"],
                            "text": clean_text(ch["text"]).strip(), "entities": [], "relations": []},
                           ensure_ascii=False) + "\n")
print(f"{len(picked)} chunks -> {a.out}")
print("répartition :", dict(collections.Counter(c["framework"] for c in picked)))
