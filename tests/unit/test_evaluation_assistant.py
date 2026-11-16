# tests/unit/test_evaluation_assistant.py
# Owner: Oussema
# Unit tests of agents/evaluation_assistant.py (feature F + reviewer). No LLM, no network.
import pytest

from agents import evaluation_assistant as ea

CHUNKS = [
    {"chunk_id": "c1", "framework": "langgraph", "score": 0.9, "url": "https://docs.example.com/eval",
     "text": "Evaluate an agent by measuring answer quality, tool usage accuracy, execution errors "
             "and latency. Hallucinations are reduced by grounding every answer in retrieved passages "
             "and by checking citations against the sources."},
    {"chunk_id": "c2", "framework": "crewai", "score": 0.7, "url": "https://docs.example.com/reliability",
     "text": "Reliability of a multi-agent system is measured with repeated runs, success rate, "
             "retries and the number of failed tool calls."},
]
SOURCES = [{"chunk_id": c["chunk_id"], "url": c["url"], "framework": c["framework"], "text": c["text"]}
           for c in CHUNKS]

GOOD_ANSWER = (
    "To evaluate an agent, measure the answer quality, the tool usage accuracy and the execution "
    "errors [1]. Hallucinations are reduced by grounding every answer in retrieved passages and by "
    "checking citations against the sources [1]. Reliability of a multi-agent system is measured with "
    "repeated runs, the success rate and the number of failed tool calls [2].\n\n"
    "Sources:\n[1] langgraph https://docs.example.com/eval\n[2] crewai https://docs.example.com/reliability"
)


# ----------------------------------------------------------------------------- run()
def test_run_builds_prompt_with_instructions_and_returns_sources(monkeypatch):
    seen = {}

    def fake_build_prompt(question, chunks, instructions=None):
        seen["instructions"] = instructions
        return "PROMPT"

    def fake_llm(prompt, system=None):
        seen["prompt"], seen["system"] = prompt, system
        return "an answer [1]"

    monkeypatch.setattr(ea, "build_prompt", fake_build_prompt)
    monkeypatch.setattr(ea, "call_llm", fake_llm)

    out = ea.run({"question": "How do I evaluate my agent?", "chunks": CHUNKS})

    assert out["answer"] == "an answer [1]"
    assert seen["instructions"] == ea.INSTRUCTIONS
    assert seen["prompt"] == "PROMPT" and seen["system"]
    assert [s["chunk_id"] for s in out["sources"]] == ["c1", "c2"]          # same order as the prompt numbers
    assert set(out["sources"][0]) == {"chunk_id", "url", "framework", "text"}


def test_run_without_chunks_does_not_call_the_llm(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("LLM must not be called without context")

    monkeypatch.setattr(ea, "call_llm", boom)
    out = ea.run({"question": "How do I evaluate my agent?", "chunks": []})
    assert out == {"answer": ea.NO_CONTEXT_ANSWER, "sources": []}


# ----------------------------------------------------------------------------- review()
def test_review_accepts_a_grounded_cited_answer():
    out = ea.review({"answer": GOOD_ANSWER, "sources": SOURCES, "chunks": CHUNKS})
    assert out == {"review": {"ok": True, "issues": []}}


def test_review_flags_missing_sources():
    out = ea.review({"answer": "Some answer.", "sources": []})["review"]
    assert out["ok"] is False
    assert "answer has no supporting sources" in out["issues"]


def test_review_flags_empty_answer():
    out = ea.review({"answer": "   ", "sources": SOURCES})["review"]
    assert out["ok"] is False and out["issues"] == ["the answer is empty"]


def test_review_accepts_honest_no_context_answer():
    out = ea.review({"answer": ea.NO_CONTEXT_ANSWER, "sources": []})["review"]
    assert out == {"ok": True, "issues": []}


def test_review_short_answer_without_citation_is_accepted():
    out = ea.review({"answer": "LangGraph builds stateful agents.", "sources": SOURCES, "chunks": CHUNKS})
    assert out["review"]["ok"] is True


def test_review_flags_long_answer_without_any_citation():
    answer = GOOD_ANSWER.split("\n\nSources:")[0].replace(" [1]", "").replace(" [2]", "")
    out = ea.review({"answer": answer, "sources": SOURCES, "chunks": CHUNKS})["review"]
    assert out["ok"] is False
    assert any("does not cite" in i for i in out["issues"])


def test_review_source_url_counts_as_citation():
    answer = GOOD_ANSWER.replace(" [1]", "").replace(" [2]", "")      # keeps the 'Sources:' URLs
    out = ea.review({"answer": answer, "sources": SOURCES, "chunks": CHUNKS})["review"]
    assert out["ok"] is True


def test_review_flags_citation_out_of_range():
    answer = GOOD_ANSWER + "\nSee also [7]."
    out = ea.review({"answer": answer, "sources": SOURCES, "chunks": CHUNKS})["review"]
    assert out["ok"] is False
    assert any("[7]" in i for i in out["issues"])


def test_review_ignores_brackets_inside_code():
    answer = GOOD_ANSWER + "\n```python\nitems = data[9]\n```"
    out = ea.review({"answer": answer, "sources": SOURCES, "chunks": CHUNKS})["review"]
    assert out["ok"] is True


def test_review_flags_invented_url():
    answer = GOOD_ANSWER + "\nMore: https://made-up.example.org/guide"
    out = ea.review({"answer": answer, "sources": SOURCES, "chunks": CHUNKS})["review"]
    assert out["ok"] is False
    assert any("made-up.example.org" in i for i in out["issues"])


def test_review_url_match_ignores_trailing_slash_and_fragment():
    answer = GOOD_ANSWER + "\nMore: https://docs.example.com/eval/#section."
    assert ea.review({"answer": answer, "sources": SOURCES, "chunks": CHUNKS})["review"]["ok"] is True


def test_review_flags_ungrounded_answer():
    answer = (
        "Quantum entanglement enables teleportation between superconducting qubits, because "
        "photons traverse optical fibers while cryogenic refrigerators stabilise transmon "
        "resonators across laboratory benches [1]. Chocolate fountains improve morale during "
        "marathon debugging sessions, according to bakery researchers [2]."
    )
    out = ea.review({"answer": answer, "sources": SOURCES, "chunks": CHUNKS})["review"]
    assert out["ok"] is False
    assert any("low overlap" in i for i in out["issues"])


def test_grounding_score_is_none_for_tiny_answers():
    assert ea.grounding_score("Short answer.", "some context about agents") is None


def test_review_never_raises():
    out = ea.review({"answer": 123, "sources": "oops"})["review"]     # malformed state
    assert out["ok"] is False and out["issues"]


# ----------------------------------------------------------------------------- optional LLM judge
def test_judge_is_off_by_default(monkeypatch):
    monkeypatch.delenv("REVIEW_USE_LLM", raising=False)

    def boom(*a, **k):
        raise AssertionError("judge must be off by default")

    monkeypatch.setattr(ea, "call_llm", boom)
    assert ea.review({"answer": GOOD_ANSWER, "sources": SOURCES, "chunks": CHUNKS})["review"]["ok"] is True


def test_judge_can_reject_an_answer(monkeypatch):
    monkeypatch.setenv("REVIEW_USE_LLM", "1")
    monkeypatch.setattr(ea, "call_llm",
                        lambda p, system=None: 'ok {"supported": false, "issues": ["claims 99% accuracy"]}')
    out = ea.review({"answer": GOOD_ANSWER, "sources": SOURCES, "chunks": CHUNKS})["review"]
    assert out["ok"] is False
    assert out["issues"] == ["judge: claims 99% accuracy"]


def test_judge_failure_is_ignored(monkeypatch):
    monkeypatch.setenv("REVIEW_USE_LLM", "1")

    def broken(*a, **k):
        raise RuntimeError("no LLM")

    monkeypatch.setattr(ea, "call_llm", broken)
    assert ea.review({"answer": GOOD_ANSWER, "sources": SOURCES, "chunks": CHUNKS})["review"]["ok"] is True


@pytest.mark.parametrize("raw", ['{"supported": true, "issues": []}', "not json at all"])
def test_judge_accepts_supported_or_unparsable(monkeypatch, raw):
    monkeypatch.setenv("REVIEW_USE_LLM", "1")
    monkeypatch.setattr(ea, "call_llm", lambda p, system=None: raw)
    assert ea.review({"answer": GOOD_ANSWER, "sources": SOURCES, "chunks": CHUNKS})["review"]["ok"] is True
