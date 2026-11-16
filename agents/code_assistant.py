# agents/code_assistant.py
# Owner: Ghassen
# Role: Code Assistant - feature D (code examples, project structure, debugging).

from agents.state import CopilotState
from generation.answer_generator import generate_answer

INSTRUCTIONS = (
    "Help the user implement their agentic system: give runnable code examples for the "
    "framework in the context, a project structure when relevant, and explain errors with "
    "a corrected version. Only use APIs that appear in the context and cite the sources."
)


def run(state: CopilotState) -> dict:
    result = generate_answer(
        state["question"],
        state.get("chunks", []),
        instructions=INSTRUCTIONS,
    )
    return {"answer": result["answer"], "sources": result["sources"]}