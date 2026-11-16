# graph/extractors/dictionary.py - extracteur n°1 : dictionnaire (entités) + règles (relations)
from graph.entity_extractor import extract_entities
from graph.relation_extractor import extract_relations


class DictionaryExtractor:
    name = "dictionary"

    def extract(self, chunk: dict) -> dict:
        ents = extract_entities(chunk)
        return {"entities": ents, "relations": extract_relations(chunk, ents)}
