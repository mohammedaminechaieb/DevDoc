# agents/intent_analyzer.py
# Role: Intent Analyzer - understands what the user needs.

from agents.state import INTENTS, CopilotState

# Cheap fallback used when the LLM is unavailable (and as a sanity check in tests)
KEYWORDS = {
    "code":      ["code", "implement", "error", "bug", "exception", "traceback", "example", "snippet", "fix"],
    "design":    ["architecture", "design", "concevoir", "how should i build", "structure my"],
    "recommend": ["which framework", "recommend", "compare", " vs ", "versus", "choose", "better"],
    "evaluate":  ["evaluate", "evaluation", "hallucination", "reliability", "metric", "benchmark", "measure"],
    "explore":   ["workflow", "flow", "step by step", "visualize", "visualise", "transition"],
}


def classify_keywords(question: str) -> str:
    q = f" {question.lower()} "
    for intent, words in KEYWORDS.items():
        if any(w in q for w in words):
            return intent
    return "learn"


def run(state: CopilotState) -> dict:
    # TODO: ask the LLM to pick one of INTENTS and list the entities (concepts, frameworks)
    #       named in the question; fall back to classify_keywords() on failure.
    assert set(KEYWORDS) <= set(INTENTS)
    return {"intent": classify_keywords(state["question"]), "entities": []}
