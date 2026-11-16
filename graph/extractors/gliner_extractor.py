# graph/extractors/gliner_extractor.py - extracteur n°2 : GLiNER (entités, zero-shot)
#
# GLiNER reçoit des LABELS en langage naturel et trouve les spans correspondants, sans entraînement.
# Ici les labels = les types de nœuds du schéma (graph.schema.NODE_TYPES) ; normalize_type() les
# ramène ensuite au type canonique. Un chunk est découpé en fenêtres (limite de longueur du modèle).
#
# Installation : pip install gliner      Modèle par défaut : urchade/gliner_medium-v2.1
# NB : écrit d'après l'API publique de GLiNER (predict_entities) ; non exécuté sur un vrai modèle
#      dans l'environnement de développement (pas d'accès à Hugging Face) -> à valider chez toi.

from graph.entity_extractor import clean_text
from graph.extractors.base import make_entity, windows
from graph.normalize import norm_key
from graph.validate import is_valid_entity_name

# Libellés naturels, un par type de nœud du schéma (re-mappés par normalize_type / TYPE_SYNONYMS)
DEFAULT_LABELS = ["framework", "ai agent", "language model", "tool", "api", "protocol", "concept",
                  "technique", "component", "architecture", "database", "data structure",
                  "programming language", "platform", "task", "metric", "artifact", "dataset"]
STOP = {"this", "that", "it", "they", "you", "we", "the", "a", "an"}


class GlinerExtractor:
    name = "gliner"

    def __init__(self, model=None, model_name="urchade/gliner_medium-v2.1", threshold=0.5,
                 labels=None, max_chars=1200):
        self._model, self.model_name = model, model_name
        self.threshold, self.labels, self.max_chars = threshold, labels or DEFAULT_LABELS, max_chars

    @property
    def model(self):
        if self._model is None:
            from gliner import GLiNER
            self._model = GLiNER.from_pretrained(self.model_name)
        return self._model

    def extract(self, chunk: dict) -> dict:
        best = {}  # clé normalisée -> entité (on garde le meilleur score, on compte les occurrences)
        for _, w in windows(clean_text(chunk.get("text", "")), self.max_chars):
            for p in self.model.predict_entities(w, self.labels, threshold=self.threshold):
                text = p["text"].strip()
                if text.lower() in STOP or not is_valid_entity_name(text):
                    continue
                key = norm_key(text)
                if key in best:
                    best[key]["count"] += 1
                    if p["score"] > best[key]["confidence"]:
                        best[key].update(make_entity(text, p["label"], chunk, "gliner", p["score"], best[key]["count"]))
                else:
                    best[key] = make_entity(text, p["label"], chunk, "gliner", p["score"])
        return {"entities": list(best.values()), "relations": []}
