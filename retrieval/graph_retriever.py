# retrieval/graph_retriever.py
# Owner: Oussema

from graph.queries import query_entity_chunks, query_related_entities


def retrieve_graph(query: str, k: int = 5) -> list[dict]:
    # TODO: extract entities from query, traverse graph, return related chunks
    # Returns: [{chunk_id, text, url, framework, score}]
    raise NotImplementedError
