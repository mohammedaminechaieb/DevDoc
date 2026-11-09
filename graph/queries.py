# graph/queries.py
# Owner: Oussema
#
# Cypher helpers used by retrieval/graph_retriever.py and agents/knowledge_retriever.py


def query_related_entities(driver, entity_name: str, depth: int = 2) -> list[dict]:
    # TODO: return nodes related to entity_name up to depth hops
    raise NotImplementedError


def query_entity_chunks(driver, entity_name: str) -> list[str]:
    # TODO: return chunk_ids that mention this entity (MENTIONED_IN)
    raise NotImplementedError


def query_subgraph(driver, entity_names: list[str], depth: int = 1) -> dict:
    # TODO: return {nodes: [...], edges: [...]} around the entities, for the GraphViewer
    raise NotImplementedError
