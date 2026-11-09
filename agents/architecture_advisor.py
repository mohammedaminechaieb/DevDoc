# agents/architecture_advisor.py
# Owner: Mariem
# Role: Architecture Advisor - features B (framework recommendation) and C (architecture designer).

from agents.state import CopilotState

INSTRUCTIONS = (
    "Propose an agentic architecture for the user's need. Give: the architecture type "
    "(single agent, multi-agent or hybrid workflow), the agents and their responsibilities, "
    "the tools, the interactions between agents, memory/state management, the execution "
    "workflow and the recommended frameworks, comparing alternatives. Cite the sources."
)


def run(state: CopilotState) -> dict:
    # TODO: build_prompt(question, chunks, INSTRUCTIONS) -> call_llm -> {answer, sources}
    raise NotImplementedError
