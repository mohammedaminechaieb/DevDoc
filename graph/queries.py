# graph/queries.py
# Cross-module owner: Ghassen
#
# Ghassen writes this because he uses these helpers directly
# in retrieval/graph_retriever.py that he also owns indirectly.

def query_related_entities(driver, entity_name: str, depth: int = 2) -> list[dict]:
    # TODO: return nodes related to entity_name up to depth hops
    raise NotImplementedError

def query_entity_chunks(driver, entity_name: str) -> list[str]:
    # TODO: return chunk_ids that mention this entity
    raise NotImplementedError
