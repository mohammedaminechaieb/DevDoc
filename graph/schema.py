# graph/schema.py
# Owner: Aya
#
# Knowledge-graph schema of the Agentic AI Copilot (NLP.pdf section 5).
# Every relationship keeps its provenance (chunk_id, url) so answers can cite it.

# Node label -> seed entities (extend while reading the corpus)
NODE_LABELS = {
    "Concept":    ["AI Agent", "Multi-Agent System", "Planning", "Memory", "Tool Calling",
                   "Function Calling", "RAG", "GraphRAG", "Orchestration", "Reasoning"],
    "Framework":  ["LangGraph", "LangChain", "CrewAI", "AutoGen", "OpenAI Agents SDK",
                   "Anthropic API"],
    "Component":  ["Agent", "Tool", "State", "Node", "Edge", "Workflow", "LLM", "Crew",
                   "Task", "Checkpointer"],
    "Technology": ["MCP", "API", "Vector Database", "Embeddings"],
    "Technique":  ["Reflection", "Routing", "Retrieval", "ReAct", "Human-in-the-loop"],
}

# Each corpus chunk is also a node, so entities point back to their source
CHUNK_LABEL = "Chunk"  # properties: chunk_id, url, framework, concept, component, version

RELATION_TYPES = [
    "IMPLEMENTS",      # LangGraph IMPLEMENTS Workflow
    "USES",            # Agent USES Tool, Agent USES LLM, RAG USES Vector Database
    "HAS",             # Agent HAS Memory
    "DELEGATES_TO",    # Agent DELEGATES_TO Agent
    "CONTAINS",        # Workflow CONTAINS Node
    "CONNECTS",        # MCP CONNECTS Agent -> Tool
    "SUPPORTS",        # Framework SUPPORTS Concept / Technique
    "ALTERNATIVE_TO",  # Framework ALTERNATIVE_TO Framework (comparisons)
    "MENTIONED_IN",    # any entity -> Chunk (provenance)
]

# Properties stored on every relationship (except MENTIONED_IN)
RELATION_PROPERTIES = ["chunk_id", "url", "framework", "version", "confidence"]
