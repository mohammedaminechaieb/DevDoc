# agents/code_assistant.py
# Role: Code Assistant - feature D (code examples, project structure, debugging).

from agents.state import CopilotState

INSTRUCTIONS = (
    "Help the user implement their agentic system: give runnable code examples for the "
    "framework in the context, a project structure when relevant, and explain errors with "
    "a corrected version. Only use APIs that appear in the context and cite the sources."
)


def run(state: CopilotState) -> dict:
    # TODO: build_prompt(question, chunks, INSTRUCTIONS) -> call_llm -> {answer, sources}
    raise NotImplementedError
