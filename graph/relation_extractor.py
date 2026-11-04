# graph/relation_extractor.py
# Primary owner: Oussema
#
# Input:  chunk dict + entities list from extract_entities()
# Output: list[{source, target, relation, chunk_id}]

def extract_relations(chunk: dict, entities: list[dict]) -> list[dict]:
    # TODO: rule-based + LLM relation extraction
    raise NotImplementedError
