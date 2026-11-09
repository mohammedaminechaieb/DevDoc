# agents/orchestrator.py
# Owner: Amine
# LangGraph orchestrator (NLP.pdf section 6).
#
#   START -> intent_analyzer -> knowledge_retriever -> (route by intent)
#            -> responder | architecture_advisor | code_assistant | evaluation_assistant
#            -> reviewer -> END

from langgraph.graph import END, START, StateGraph

from agents import (
    architecture_advisor,
    code_assistant,
    evaluation_assistant,
    intent_analyzer,
    knowledge_retriever,
    responder,
)
from agents.state import CopilotState
from config.settings import TOP_K

ROUTES = {
    "learn":     "responder",
    "explore":   "responder",
    "recommend": "architecture_advisor",
    "design":    "architecture_advisor",
    "code":      "code_assistant",
    "evaluate":  "evaluation_assistant",
}
SPECIALISTS = sorted(set(ROUTES.values()))


def route_by_intent(state: CopilotState) -> str:
    return ROUTES.get(state.get("intent", ""), "responder")


def build_graph():
    g = StateGraph(CopilotState)
    g.add_node("intent_analyzer", intent_analyzer.run)
    g.add_node("knowledge_retriever", knowledge_retriever.run)
    g.add_node("responder", responder.run)
    g.add_node("architecture_advisor", architecture_advisor.run)
    g.add_node("code_assistant", code_assistant.run)
    g.add_node("evaluation_assistant", evaluation_assistant.run)
    g.add_node("reviewer", evaluation_assistant.review)

    g.add_edge(START, "intent_analyzer")
    g.add_edge("intent_analyzer", "knowledge_retriever")
    g.add_conditional_edges("knowledge_retriever", route_by_intent, SPECIALISTS)
    for name in SPECIALISTS:
        g.add_edge(name, "reviewer")
    g.add_edge("reviewer", END)
    return g.compile()


_app = None


def run_copilot(question: str, top_k: int = TOP_K, use_graph: bool = True,
                history: list[dict] | None = None) -> CopilotState:
    global _app
    if _app is None:
        _app = build_graph()
    return _app.invoke({
        "question": question,
        "top_k": top_k,
        "use_graph": use_graph,
        "history": history or [],
    })
