# graph/relation_extractor.py
# Owner: Oussema
#
# Input:  chunk dict + entities list from extract_entities()
# Output: list[{source, target, relation, chunk_id, url, framework, version, confidence}]
#         relation is one of graph.schema.RELATION_TYPES

def extract_relations(chunk: dict, entities: list[dict]) -> list[dict]:
    # TODO: rule-based patterns (e.g. "<Agent> uses <Tool>") + LLM extraction,
    #       keep only relations whose both ends are in `entities`
    raise NotImplementedError
