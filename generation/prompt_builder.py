# generation/prompt_builder.py
# Owner: Ghassen

SYSTEM_PROMPT = (
    "You are Agentic AI Copilot, an expert assistant that helps developers learn, design "
    "and build Agentic AI systems (LangGraph, CrewAI, AutoGen, MCP, tool calling, memory, "
    "RAG...). Answer ONLY from the provided context. "
    "If the answer is not in the context, say so explicitly. "
    "Always cite the source URL and framework."
)


def build_prompt(query: str, chunks: list[dict], instructions: str | None = None) -> str:
    # TODO: format chunks as numbered context blocks [1] (framework, url) text,
    #       add the agent-specific `instructions` if given, then append the question
    raise NotImplementedError
