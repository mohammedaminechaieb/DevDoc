# agents/state.py
# Owner: Amine
# Shared state passed between the LangGraph nodes.

from typing import TypedDict

# One intent per feature of NLP.pdf section 4
INTENTS = {
    "learn":     "A - explain an Agentic AI concept",
    "recommend": "B - recommend / compare frameworks and technologies",
    "design":    "C - turn a project idea into an agentic architecture",
    "code":      "D - code examples, project structure, debugging errors",
    "explore":   "E - explain / visualise how an agentic workflow runs",
    "evaluate":  "F - evaluation, reliability, hallucinations, performance",
}


class CopilotState(TypedDict, total=False):
    # input
    question: str
    history: list[dict]       # previous turns: [{role, content}]
    top_k: int
    use_graph: bool
    # intent_analyzer
    intent: str               # one of INTENTS
    entities: list[str]       # concepts / frameworks named in the question
    # knowledge_retriever
    chunks: list[dict]        # [{chunk_id, text, url, framework, score, ...}]
    graph: dict               # {nodes: [...], edges: [...]} for the frontend GraphViewer
    # specialist agent
    answer: str
    sources: list[dict]       # [{chunk_id, url, framework, text}]
    # reviewer
    review: dict              # {ok: bool, issues: [str]}
