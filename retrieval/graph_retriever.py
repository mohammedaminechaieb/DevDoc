# retrieval/graph_retriever.py
# Cross-module owner: Oussema
#
# Oussema writes this because he built the graph and knows
# exactly which Cypher patterns to use here.

from graph.queries import query_related_entities, query_entity_chunks

def retrieve_graph(query: str, k: int = 5) -> list[dict]:
    # TODO: extract entities from query, traverse graph, return related chunks
    raise NotImplementedError
