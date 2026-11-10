# agents/responder.py
# Owner: Ghassen
# Answers learning (A) and workflow-explorer (E) questions with the grounded RAG answer.

from agents.state import CopilotState
from generation.answer_generator import generate_answer


def run(state: CopilotState) -> dict:
    result = generate_answer(state["question"], state.get("chunks", []))
    return {"answer": result["answer"], "sources": result["sources"]}
