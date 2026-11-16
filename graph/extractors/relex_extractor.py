# graph/extractors/relex_extractor.py - extracteur n°3 : GLiNER-Relex (entités + relations, un seul passage)
#
# D'après la fiche du modèle (knowledgator/gliner-relex-*-v1.0) :
#   entities, relations = model.inference(texts=[t], labels=[...], relations=[...],
#                                         threshold=..., relation_threshold=..., return_relations=True, flat_ner=False)
#   entities[0]  : [{text, label, score, start, end}]
#   relations[0] : [{head: {text, type, ...}, tail: {...}, relation, score}]
# Les labels de relations sont des expressions naturelles ("uses", "depends on") dérivées de
# graph.schema.RELATION_TYPES ; normalize_relation() les ramène aux relations canoniques.
# Installation : pip install gliner -U       Non exécuté sur un vrai modèle ici -> à valider chez toi.

from graph.entity_extractor import clean_text
from graph.extractors.base import make_entity, make_relation, sentence_with, windows
from graph.extractors.gliner_extractor import DEFAULT_LABELS
from graph.normalize import norm_key
from graph.validate import is_valid_entity_name
from graph.schema import UNKNOWN_RELATION_TYPE, RELATION_TYPES

RELATION_LABELS = [r.lower().replace("_", " ") for r in RELATION_TYPES if r != UNKNOWN_RELATION_TYPE]


class GlinerRelexExtractor:
    name = "relex"

    def __init__(self, model=None, model_name="knowledgator/gliner-relex-large-v1.0",
                 threshold=0.5, relation_threshold=0.5, labels=None, relation_labels=None, max_chars=1200):
        self._model, self.model_name = model, model_name
        self.threshold, self.relation_threshold, self.max_chars = threshold, relation_threshold, max_chars
        self.labels, self.relation_labels = labels or DEFAULT_LABELS, relation_labels or RELATION_LABELS

    @property
    def model(self):
        if self._model is None:
            from gliner import GLiNER
            self._model = GLiNER.from_pretrained(self.model_name)
        return self._model

    def extract(self, chunk: dict) -> dict:
        ents, rels = {}, {}
        for _, w in windows(clean_text(chunk.get("text", "")), self.max_chars):
            e_out, r_out = self.model.inference(
                texts=[w], labels=self.labels, relations=self.relation_labels,
                threshold=self.threshold, relation_threshold=self.relation_threshold,
                return_relations=True, flat_ner=False)
            for e in e_out[0]:
                if not is_valid_entity_name(e["text"]):
                    continue
                key = norm_key(e["text"])
                if key not in ents or e["score"] > ents[key]["confidence"]:
                    ents[key] = make_entity(e["text"], e["label"], chunk, "relex", e["score"])
            for r in r_out[0]:
                h, t = r["head"], r["tail"]
                if not (is_valid_entity_name(h["text"]) and is_valid_entity_name(t["text"])):
                    continue
                rel = make_relation(h["text"], t["text"], r["relation"], chunk, "relex", r["score"],
                                    evidence=sentence_with(w, h["text"], t["text"]),
                                    source_type=h.get("type", ""), target_type=t.get("type", ""))
                key = (norm_key(h["text"]), rel["relation"], norm_key(t["text"]))
                if key[0] != key[2] and (key not in rels or rel["confidence"] > rels[key]["confidence"]):
                    rels[key] = rel
        return {"entities": list(ents.values()), "relations": list(rels.values())}
