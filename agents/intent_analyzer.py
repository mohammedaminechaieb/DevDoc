# agents/intent_analyzer.py
# Owner: Amine
# Role: Intent Analyzer - understands what the user needs.
import json
import re

from agents.state import INTENTS, CopilotState
from generation.llm_client import call_llm
from graph.schema import NODE_LABELS

# Cheap fallback used when the LLM is unavailable (and as a sanity check in tests)
KEYWORDS = {
    "code":      ["code", "implement", "error", "bug", "exception", "traceback", "example", "snippet", "fix"],
    "design":    ["architecture", "design", "concevoir", "how should i build", "structure my"],
    "recommend": ["which framework", "recommend", "compare", " vs ", "versus", "choose", "better"],
    "evaluate":  ["evaluate", "evaluation", "hallucination", "reliability", "metric", "benchmark", "measure"],
    "explore":   ["workflow", "flow", "step by step", "visualize", "visualise", "transition"],
}

KNOWN_ENTITIES = sorted({n for names in NODE_LABELS.values() for n in names}, 
                        key=len, reverse=True)
INTENT_PROMPT = """You classify questions asked to an Agentic AI copilot.

Intents (pick exactly one key):
{intents}

Known entities (frameworks, concepts, components): {entities}

Previous turns:
{history}

Question: {question}

Reply with ONLY a JSON object, no explanation:
{{"intent": "<intent key>", "entities": ["<known entity>", ...]}}"""

def classify_keywords(question: str) -> str:
    q = f" {question.lower()} "
    for intent, words in KEYWORDS.items():
        if any(w in q for w in words):
            return intent
    return "learn"

def extract_entities(question: str) -> list[str]:
    q = question.lower()
    found: list[str] = []
    for entity in KNOWN_ENTITIES:
        if re.search(rf"(?<![a-z0-9]){re.escape(entity.lower())}s?(?![a-z0-9])", q):
            if not any(entity.lower() in e.lower() for e in found):
                found.append(entity)
    return found

def _format_history(history: list[dict] | None, max_turns: int = 4) -> str:
    turns = (history or [])[-max_turns:]
    lines = [f"{t.get('role', 'user')}: {str(t.get('content', ''))[:200]}" for t in turns]
    return "\n".join(lines) or "(none)"

def classify_llm(question: str, history: list[dict] | None = None) -> dict | None:
    prompt = INTENT_PROMPT.format(
        intents="\n".join(f"- {k}: {v}" for k, v in INTENTS.items()),
        entities=", ".join(KNOWN_ENTITIES),
        history=_format_history(history),
        question=question,
    )
    try:
        raw = call_llm(prompt, system="You are a strict JSON classifier.")
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0)) if match else {}
    except Exception as e:
        return None
    intent = data.get("intent")
    if intent not in INTENTS:
        return None
    entities = [e for e in data.get("entities", []) if isinstance(e, str) 
                and e in KNOWN_ENTITIES]
    return {"intent": intent, "entities": entities}

def run(state: CopilotState) -> dict:
    question = state["question"]
    result = classify_llm(question, state.get("history"))
    if result is None:
        result = {
            "intent": classify_keywords(question),
            "entities": [],
        }
    entities = list(dict.fromkeys(result["entities"] + extract_entities(question))) 
    return {"intent": result["intent"], "entities": entities} 
