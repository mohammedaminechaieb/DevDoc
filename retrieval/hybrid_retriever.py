# retrieval/hybrid_retriever.py
# Owner: Mariem

from retrieval.faiss_retriever import search_faiss
# from retrieval.graph_retriever import search_graph  # TODO: Uncomment when Aya finishes

def retrieve(query: str, k: int = 5, use_graph: bool = True) -> list[dict]:
    """
    Main entry point for the orchestrator. 
    Currently mocks graph retrieval until Neo4j is ready.
    """
    print(f"\n--- Hybrid Retrieval Triggered ---")
    print(f"Query: '{query}'")
    
    # 1. Always execute Vector Search
    print("Executing Vector Search...")
    vector_results = search_faiss(query, k=k)
    
    # 2. Execute Graph Search (Mocked for now)
    graph_results = []
    if use_graph:
        print("Warning: Graph retrieval is mocked. Returning empty graph list.")
        # graph_results = search_graph(query) 
        pass
        
    # 3. Merge and Deduplicate (Will matter when graph is active)
    seen_ids = set()
    final_chunks = []
    
    for chunk in vector_results + graph_results:
        chunk_id = chunk["chunk_id"]
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            final_chunks.append(chunk)
            
    # Return the top K combined results
    return final_chunks[:k]