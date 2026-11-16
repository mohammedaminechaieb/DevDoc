# scripts/explore_entities.py - mesure la qualité de l'extracteur sur tout le corpus
import collections, jsonlines
from config.settings import CORPUS_PATH
from graph.entity_extractor import extract_entities

by_ent, per_chunk, fw_cov = collections.Counter(), [], collections.defaultdict(list)
with jsonlines.open(CORPUS_PATH) as r:
    for ch in r:
        ents = extract_entities(ch)
        per_chunk.append(len(ents)); fw_cov[ch["framework"]].append(len(ents))
        for e in ents:
            by_ent[(e["name"], e["canonical_type"])] += 1

n = len(per_chunk)
print(f"chunks: {n} | sans aucune entité: {sum(1 for x in per_chunk if x==0)} "
      f"| moyenne/chunk: {sum(per_chunk)/n:.2f}")
print("\nTop 25 entités (nb de chunks) :")
for (name, t), c in by_ent.most_common(25):
    print(f"  {c:5d}  {name:22s} {t}")
print("\nEntités des graines JAMAIS trouvées :")
from graph.vocabulary import ENTITIES
seen = {k[0] for k in by_ent}
print([x for x in ENTITIES if x not in seen])
print("\nMoyenne d'entités par framework :")
for fw, v in fw_cov.items():
    print(f"  {fw:12s} {sum(v)/len(v):.2f}")
