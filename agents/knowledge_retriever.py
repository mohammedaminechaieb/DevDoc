# agents/knowledge_retriever.py
# Owner: Ghassen
# Role: Knowledge Retrieval - queries the docs through FAISS + the Neo4j graph.

from agents.state import CopilotState
from retrieval.hybrid_retriever import retrieve


def run(state: CopilotState) -> dict:
    chunks = retrieve(state["question"], k=state.get("top_k", 5),
                      use_graph=state.get("use_graph", True))
    # TODO: also return the subgraph around state["entities"] for the frontend GraphViewer
    return {"chunks": chunks, "graph": {"nodes": [], "edges": []}}
