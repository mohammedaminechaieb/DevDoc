# scripts/explore_relations.py - qualité des relations : volumes + exemples à relire à la main
import collections, random, jsonlines
from config.settings import CORPUS_PATH
from graph.entity_extractor import extract_entities
from graph.relation_extractor import extract_relations

by_rel, triples, ex = collections.Counter(), collections.Counter(), collections.defaultdict(list)
n = with_rel = 0
with jsonlines.open(CORPUS_PATH) as r:
    for ch in r:
        n += 1
        rs = extract_relations(ch, extract_entities(ch))
        with_rel += bool(rs)
        for x in rs:
            by_rel[x["relation"]] += 1
            triples[(x["source"], x["relation"], x["target"])] += 1
            ex[x["relation"]].append(x)
print(f"chunks avec >=1 relation: {with_rel}/{n}")
print("\nPar type :", dict(by_rel.most_common()))
print("\nTop 15 triplets :")
for (s, r, t), c in triples.most_common(15):
    print(f"  {c:4d}  {s} -{r}-> {t}")
random.seed(0)
print("\n=== À RELIRE : 3 exemples au hasard par type (la précision se juge ici) ===")
for rel, lst in ex.items():
    for x in random.sample(lst, min(3, len(lst))):
        print(f"[{rel}] {x['source']} -> {x['target']} (conf {x['confidence']})\n    {x['evidence'][:200]}")
