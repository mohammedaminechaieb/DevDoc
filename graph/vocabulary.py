# graph/vocabulary.py
# Owner: Aya
#
# Vocabulaire de l'extracteur par dictionnaire (étape "dictionnaire" du pipeline).
# Séparé de schema.py : le schéma est ouvert (types/relations extensibles),
# alors que ce fichier est une liste de termes CONNUS qu'on veut retrouver à coup sûr.
# Les graines de schema.SEED_ENTITIES sont toujours incluses.

from graph.schema import NODE_TYPES, SEED_ENTITIES

# Entités supplémentaires, groupées par type canonique du schéma.
EXTRA_ENTITIES = {
    "Concept":   ["Orchestration", "Embeddings"],
    "Agent":     ["Agent", "AI Agent"],
    "Technique": ["Tool Calling", "Function Calling", "Reflection", "Routing", "Retrieval",
                  "ReAct", "Human-in-the-loop"],
    "Component": ["State", "StateGraph", "Node", "Edge", "Workflow", "Checkpointer", "Crew"],
    "Tool":      ["Tool"],
    "Model":     ["LLM"],
    "API":       ["API", "Anthropic API"],
    "DataStore": ["Vector Database"],
    "Language":  ["JavaScript", "TypeScript"],
    "Task":      ["Task"],
}

# Ajouts mesurés sur le corpus (nb de chunks entre parenthèses, nov. 2026) : termes NON ambigus uniquement.
# Les termes génériques ("Flow", "Process", "Store", "Command") sont laissés à GLiNER / au LLM.
EXTRA_ENTITIES_CORPUS = {
    "Platform":  ["LangSmith",          # 151
                  "OpenTelemetry",      # 32
                  "Docker"],            # 22
    "Framework": ["Pydantic",           # 168
                  "FastAPI", "LlamaIndex"],
    "Protocol":  ["HTTP", "OAuth", "JSON-RPC", "SSE", "Streamable HTTP"],
    "API":       ["Responses API", "Chat Completions API"],
    "Model":     ["Claude Opus", "Claude Sonnet", "Claude Haiku", "GPT-4o", "GPT-4"],
    "Technique": ["Structured Outputs", "Streaming", "Guardrails", "Chain-of-Thought", "Tree of Thoughts"],
    "Component": ["Middleware", "Subgraph", "MessagesState", "InMemorySaver", "BaseTool", "Callback"],
    "DataStore": ["MongoDB", "PostgreSQL", "SQLite", "ChromaDB"],
    "Language":  ["SQL"],
    "Tool":      ["Tavily"],
}
for _t, _names in EXTRA_ENTITIES_CORPUS.items():
    EXTRA_ENTITIES.setdefault(_t, []).extend(_names)

# Forme de surface (minuscules) -> nom canonique. À enrichir en lisant le corpus.
ALIASES = {
    "tool use": "Tool Calling", "tool calling": "Tool Calling", "tool call": "Tool Calling",
    "function calling": "Function Calling", "function call": "Function Calling",
    "multi-agent": "Multi-Agent System", "multi agent": "Multi-Agent System",
    "multiagent": "Multi-Agent System",
    "model context protocol": "MCP",
    "vector store": "Vector Database", "vector database": "Vector Database", "vector db": "Vector Database",
    "human in the loop": "Human-in-the-loop", "human-in-the-loop": "Human-in-the-loop", "hitl": "Human-in-the-loop",
    "retrieval-augmented generation": "RAG", "retrieval augmented generation": "RAG",
    "graph rag": "GraphRAG",
    "large language model": "LLM",
    "openai agents sdk": "OpenAI Agents SDK", "agents sdk": "OpenAI Agents SDK",
    "claude api": "Anthropic API", "anthropic api": "Anthropic API",
    "agentic workflow": "Workflow",
    "state graph": "StateGraph", "stategraph": "StateGraph",
    "crewai": "CrewAI", "langgraph": "LangGraph", "langchain": "LangChain", "autogen": "AutoGen",
    "json rpc": "JSON-RPC", "jsonrpc": "JSON-RPC", "server-sent events": "SSE", "server sent events": "SSE",
    "chat completions": "Chat Completions API", "chat completions api": "Chat Completions API",
    "postgres": "PostgreSQL", "chroma": "ChromaDB", "chain of thought": "Chain-of-Thought",
    "structured output": "Structured Outputs", "subgraphs": "Subgraph", "guardrail": "Guardrails",
    "callbacks": "Callback", "tree-of-thoughts": "Tree of Thoughts",
}

# Acronymes / mots ambigus : casse exacte exigée ("ReAct" != "React", le framework JS).
CASE_SENSITIVE = {"API", "LLM", "RAG", "MCP", "ReAct", "GraphRAG", "HTTP", "SSE", "SQL", "OAuth", "GPT-4", "GPT-4o"}

# Métadonnée `framework` du corpus -> (entité, type).
FRAMEWORK_META = {
    "langgraph": ("LangGraph", "Framework"),
    "langchain": ("LangChain", "Framework"),
    "crewai": ("CrewAI", "Framework"),
    "autogen": ("AutoGen", "Framework"),
    "openai": ("OpenAI Agents SDK", "Framework"),
    "anthropic": ("Anthropic API", "API"),
    "mcp": ("MCP", "Protocol"),
}


def _merge() -> dict:
    ents = {}
    for source in (SEED_ENTITIES, EXTRA_ENTITIES):
        for etype, names in source.items():
            assert etype in NODE_TYPES, f"type inconnu dans le vocabulaire : {etype}"
            for n in names:
                ents.setdefault(n, etype)  # les graines du schéma ont priorité
    return ents


ENTITIES = _merge()   # nom canonique -> type canonique
