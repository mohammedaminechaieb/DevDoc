# tests/unit/test_generator.py
# Owner: Ghassen
from unittest.mock import MagicMock, patch

import pytest

from agents import architecture_advisor, code_assistant, responder
from generation.answer_generator import NO_CONTEXT_ANSWER, generate_answer
from generation.llm_client import call_llm
from generation.prompt_builder import MAX_CHUNK_CHARS, SYSTEM_PROMPT, build_prompt

CHUNKS = [{
    "chunk_id": "lg_001",
    "text": "LangGraph is a library for building stateful agents.",
    "url": "https://langchain-ai.github.io/langgraph/",
    "framework": "langgraph", "score": 0.95,
}]


@pytest.fixture(autouse=True)
def mock_llm_and_reranker():
    """No network and no dependency on the reranker (Mariem) in unit tests."""
    with patch("generation.answer_generator.call_llm", return_value="mock answer") as llm, \
         patch("generation.answer_generator.rerank",
               side_effect=lambda q, c, **kwargs: c):   # accepte top_k
        yield llm


@pytest.fixture
def mock_llm(mock_llm_and_reranker):
    """Alias : les tests qui vérifient les appels au LLM utilisent `mock_llm`."""
    return mock_llm_and_reranker


# ---------- generate_answer ----------

def test_returns_dict():
    assert isinstance(generate_answer("What is LangGraph?", CHUNKS), dict)


def test_has_required_keys():
    r = generate_answer("What is LangGraph?", CHUNKS)
    assert "answer" in r and "sources" in r and "query" in r


def test_answer_comes_from_llm():
    r = generate_answer("What is LangGraph?", CHUNKS)
    assert r["answer"] == "mock answer"
    assert r["query"] == "What is LangGraph?"


def test_sources_format():
    r = generate_answer("What is LangGraph?", CHUNKS)
    assert len(r["sources"]) == 1
    source = r["sources"][0]
    assert set(source) == {"chunk_id", "url", "framework", "text"}  # no score
    assert source["chunk_id"] == "lg_001"


def test_empty_chunks_skips_llm(mock_llm):
    r = generate_answer("What is LangGraph?", [])
    assert r["answer"] == NO_CONTEXT_ANSWER
    assert r["sources"] == []
    mock_llm.assert_not_called()


def test_system_prompt_is_sent(mock_llm):
    generate_answer("What is LangGraph?", CHUNKS)
    assert mock_llm.call_args.kwargs["system"] == SYSTEM_PROMPT


def test_instructions_reach_the_prompt(mock_llm):
    generate_answer("q", CHUNKS, instructions="MY_SPECIAL_INSTRUCTIONS")
    assert "MY_SPECIAL_INSTRUCTIONS" in mock_llm.call_args.args[0]


# ---------- build_prompt ----------

def test_prompt_numbers_chunks_with_metadata():
    prompt = build_prompt("q", CHUNKS + CHUNKS)
    assert "[1] (framework: langgraph, url: https://langchain-ai.github.io/langgraph/)" in prompt
    assert "[2]" in prompt


def test_prompt_question_is_last():
    prompt = build_prompt("What is LangGraph?", CHUNKS)
    assert prompt.rstrip().endswith("What is LangGraph?")


def test_prompt_without_instructions_has_no_instructions_block():
    assert "INSTRUCTIONS:" not in build_prompt("q", CHUNKS)


def test_prompt_with_instructions():
    assert "INSTRUCTIONS:\nBe brief." in build_prompt("q", CHUNKS, "Be brief.")


def test_prompt_with_no_chunks():
    assert "no relevant passage" in build_prompt("q", [])


def test_prompt_truncates_long_chunks():
    long_chunk = [{"text": "x" * (MAX_CHUNK_CHARS * 3), "url": "u", "framework": "f"}]
    prompt = build_prompt("q", long_chunk)
    assert "x" * (MAX_CHUNK_CHARS + 1) not in prompt


def test_prompt_tolerates_missing_fields():
    prompt = build_prompt("q", [{"text": "hello"}])
    assert "unknown" in prompt and "hello" in prompt


# ---------- call_llm ----------

def test_unknown_provider_raises():
    with patch("generation.llm_client.LLM_PROVIDER", "foo"):
        with pytest.raises(ValueError):
            call_llm("hi")


def test_groq_without_key_raises():
    with patch("generation.llm_client.LLM_PROVIDER", "groq"), \
         patch("generation.llm_client.GROQ_API_KEY", ""):
        with pytest.raises(RuntimeError):
            call_llm("hi")


def test_ollama_returns_message_content():
    fake_response = MagicMock()
    fake_response.json.return_value = {"message": {"content": "hello from ollama"}}
    with patch("generation.llm_client.LLM_PROVIDER", "ollama"), \
         patch("generation.llm_client.httpx.post", return_value=fake_response):
        assert call_llm("hi", system="sys") == "hello from ollama"


# ---------- agents ----------

STATE = {"question": "How should I design a research agent system?", "chunks": CHUNKS}


@pytest.mark.parametrize("agent", [responder, architecture_advisor, code_assistant])
def test_agent_returns_answer_and_sources(agent):
    out = agent.run(STATE)
    assert out["answer"] == "mock answer"
    assert out["sources"] and out["sources"][0]["chunk_id"] == "lg_001"


@pytest.mark.parametrize("agent", [architecture_advisor, code_assistant])
def test_specialist_agents_use_their_instructions(agent, mock_llm):
    agent.run(STATE)
    assert agent.INSTRUCTIONS in mock_llm.call_args.args[0]


def test_responder_has_no_extra_instructions(mock_llm):
    responder.run(STATE)
    assert "INSTRUCTIONS:" not in mock_llm.call_args.args[0]


def test_agent_works_without_chunks_in_state(mock_llm):
    out = architecture_advisor.run({"question": "q"})
    assert out["sources"] == []
    mock_llm.assert_not_called()