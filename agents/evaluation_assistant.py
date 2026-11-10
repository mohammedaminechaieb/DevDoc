# agents/evaluation_assistant.py
# Owner: Oussema
# Role: Evaluation Assistant
#   run()    - answers feature F questions (evaluation, reliability, hallucinations)
#   review() - checks every answer before it is returned (grounding, citations)

from agents.state import CopilotState

INSTRUCTIONS = (
    "Explain how to evaluate and improve the user's agentic system: answer quality, tool "
    "usage, execution errors, hallucination mitigation, reliability and performance of "
    "multi-agent systems. Cite the sources."
)


def run(state: CopilotState) -> dict:
    # TODO: build_prompt(question, chunks, INSTRUCTIONS) -> call_llm -> {answer, sources}
    raise NotImplementedError


def review(state: CopilotState) -> dict:
    # TODO: verify the answer is supported by state["chunks"] and cites sources;
    #       list problems in issues (optionally ask the LLM as a judge).
    ok = bool(state.get("answer")) and bool(state.get("sources"))
    return {"review": {"ok": ok, "issues": [] if ok else ["answer has no supporting sources"]}}
