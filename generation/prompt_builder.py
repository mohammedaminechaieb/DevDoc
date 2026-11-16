# generation/prompt_builder.py
# Owner: Ghassen

SYSTEM_PROMPT = (
    "You are Agentic AI Copilot, an expert assistant that helps developers learn, design "
    "and build Agentic AI systems (LangGraph, CrewAI, AutoGen, MCP, tool calling, memory, "
    "RAG...). Answer ONLY from the provided context. "
    "If the answer is not in the context, say so explicitly. "
    "Always cite the source URL and framework."
)

# Max characters kept per chunk, to avoid overflowing the context window of small models
MAX_CHUNK_CHARS = 1500

CITATION_RULE = (
    "Cite your sources inline using the context numbers, e.g. [1], [2]. "
    "End your answer with a 'Sources' list giving, for each cited number, "
    "the framework and the URL."
)


def _format_chunk(index: int, chunk: dict) -> str:
    """Format one chunk as a numbered context block: [n] (framework, url) text."""
    framework = chunk.get("framework") or "unknown"
    url = chunk.get("url") or "unknown"
    text = (chunk.get("text") or "").strip()

    if len(text) > MAX_CHUNK_CHARS:
        text = text[:MAX_CHUNK_CHARS].rstrip() + "..."

    return f"[{index}] (framework: {framework}, url: {url})\n{text}"


def build_prompt(query: str, chunks: list[dict], instructions: str | None = None) -> str:
    """Build the user prompt: agent instructions + numbered context + citation rule + question."""
    parts = []

    # 1. Agent-specific instructions (architecture advisor, code assistant, ...)
    if instructions:
        parts.append(f"INSTRUCTIONS:\n{instructions}")

    # 2. Numbered context blocks
    if chunks:
        context = "\n\n".join(
            _format_chunk(i, chunk) for i, chunk in enumerate(chunks, start=1)
        )
    else:
        context = "(no relevant passage was retrieved)"
    parts.append(f"CONTEXT:\n{context}")

    # 3. Citation rule
    parts.append(CITATION_RULE)

    # 4. The question comes last
    parts.append(f"QUESTION:\n{query}")

    return "\n\n".join(parts)