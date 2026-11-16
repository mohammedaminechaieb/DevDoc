# tests/unit/test_retriever.py
# Owner: Mariem
# Unit tests for FAISS retrieval, RRF hybrid merge, cross-encoder reranking,
# and the knowledge_retriever LangGraph node.

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from retrieval.hybrid_retriever import retrieve, rrf_merge
from generation.reranker import rerank
from agents import knowledge_retriever


# ---------------------------------------------------------------------------
# Original Smoke Tests (Preserved)
# ---------------------------------------------------------------------------


def test_returns_list():
    assert isinstance(retrieve("What is LangGraph?", k=3), list)


def test_has_required_keys():
    result = retrieve("What is LangGraph?", k=1)
    if result:
        for key in ("chunk_id", "text", "url", "framework", "score"):
            assert key in result[0]


# ---------------------------------------------------------------------------
# Fixtures & Sample Data
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_vector_chunks():
    return [
        {
            "chunk_id": "lg_01",
            "text": "StateGraph compiles nodes and edges into a runnable LangGraph workflow.",
            "url": "https://langchain-ai.github.io/langgraph/concepts/",
            "framework": "langgraph",
            "score": 0.89,
        },
        {
            "chunk_id": "fa_01",
            "text": "FastAPI validates request payloads using Pydantic BaseModel schemas.",
            "url": "https://fastapi.tiangolo.com/tutorial/body/",
            "framework": "fastapi",
            "score": 0.74,
        },
        {
            "chunk_id": "dk_01",
            "text": "Docker Compose orchestrates multi-container services via docker-compose.yml.",
            "url": "https://docs.docker.com/compose/",
            "framework": "docker",
            "score": 0.65,
        },
    ]


@pytest.fixture
def sample_graph_chunks():
    # Matches Aya's graph_retriever.retrieve_graph output schema
    return [
        {
            "chunk_id": "lg_02",
            "text": "Conditional edges route execution dynamically based on CopilotState fields.",
            "url": "https://langchain-ai.github.io/langgraph/how-tos/branching/",
            "framework": "langgraph",
            "score": 1.0,
            "entities": ["StateGraph", "CopilotState"],
        },
        {
            "chunk_id": "lg_01",  # Intentional duplicate with FAISS to test RRF boost
            "text": "StateGraph compiles nodes and edges into a runnable LangGraph workflow.",
            "url": "https://langchain-ai.github.io/langgraph/concepts/",
            "framework": "langgraph",
            "score": 0.82,
            "entities": ["StateGraph"],
        },
    ]


# ---------------------------------------------------------------------------
# 1. RRF Merge & Hybrid Retriever Tests
# ---------------------------------------------------------------------------


def test_rrf_merge_deduplicates_and_boosts_shared_chunks(
    sample_vector_chunks, sample_graph_chunks
):
    merged = rrf_merge([sample_vector_chunks, sample_graph_chunks], k_rrf=60, top_k=5)

    chunk_ids = [c["chunk_id"] for c in merged]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert set(chunk_ids) == {"lg_01", "lg_02", "fa_01", "dk_01"}

    # lg_01 appears at rank 1 in FAISS and rank 2 in Graph -> highest combined RRF score
    assert merged[0]["chunk_id"] == "lg_01"
    expected_lg01_score = (1.0 / (60 + 1)) + (1.0 / (60 + 2))
    assert merged[0]["rrf_score"] == pytest.approx(expected_lg01_score)
    assert merged[0]["score"] == pytest.approx(expected_lg01_score)


def test_rrf_merge_respects_top_k(sample_vector_chunks):
    merged = rrf_merge([sample_vector_chunks], top_k=2)
    assert len(merged) == 2
    assert [c["chunk_id"] for c in merged] == ["lg_01", "fa_01"]


@patch("retrieval.hybrid_retriever.search_faiss")
def test_hybrid_retrieve_vector_only_when_use_graph_false(
    mock_search_faiss, sample_vector_chunks
):
    mock_search_faiss.return_value = sample_vector_chunks

    results = retrieve("How does StateGraph work?", k=2, use_graph=False)

    mock_search_faiss.assert_called_once_with("How does StateGraph work?", k=2)
    assert len(results) == 2
    assert results[0]["chunk_id"] == "lg_01"


@patch("retrieval.hybrid_retriever.search_faiss")
def test_hybrid_retrieve_fuses_with_eya_graph_retriever(
    mock_search_faiss, sample_vector_chunks, sample_graph_chunks, monkeypatch
):
    mock_search_faiss.return_value = sample_vector_chunks

    fake_graph_mod = types.ModuleType("retrieval.graph_retriever")
    fake_graph_mod.retrieve_graph = MagicMock(return_value=sample_graph_chunks)
    monkeypatch.setitem(sys.modules, "retrieval.graph_retriever", fake_graph_mod)

    results = retrieve("How does StateGraph work?", k=4, use_graph=True)

    fake_graph_mod.retrieve_graph.assert_called_once_with("How does StateGraph work?", k=4)
    assert len(results) == 4
    assert results[0]["chunk_id"] == "lg_01"


@patch("retrieval.hybrid_retriever.search_faiss")
def test_hybrid_retrieve_falls_back_gracefully_when_graph_unavailable(
    mock_search_faiss, sample_vector_chunks, monkeypatch
):
    mock_search_faiss.return_value = sample_vector_chunks
    monkeypatch.setitem(sys.modules, "retrieval.graph_retriever", None)

    results = retrieve("How does StateGraph work?", k=3, use_graph=True)
    assert len(results) == 3
    assert [c["chunk_id"] for c in results] == ["lg_01", "fa_01", "dk_01"]


# ---------------------------------------------------------------------------
# 2. Cross-Encoder Reranker Tests
# ---------------------------------------------------------------------------


@patch("generation.reranker._get_reranker")
def test_rerank_sorts_by_cross_encoder_score_and_preserves_metadata(
    mock_get_reranker, sample_vector_chunks
):
    mock_model = MagicMock()
    mock_model.compute_score.return_value = [1.25, -2.40, 4.80]
    mock_get_reranker.return_value = mock_model

    ranked = rerank("Docker Compose setup", sample_vector_chunks, top_k=2)

    assert len(ranked) == 2
    assert ranked[0]["chunk_id"] == "dk_01"
    assert ranked[0]["rerank_score"] == pytest.approx(4.80)
    assert ranked[0]["framework"] == "docker"
    assert ranked[0]["url"] == "https://docs.docker.com/compose/"
    assert ranked[1]["chunk_id"] == "lg_01"


@patch("generation.reranker._get_reranker")
def test_rerank_handles_single_chunk_scalar_float(mock_get_reranker, sample_vector_chunks):
    mock_model = MagicMock()
    mock_model.compute_score.return_value = 3.1415
    mock_get_reranker.return_value = mock_model

    ranked = rerank("StateGraph", [sample_vector_chunks[0]], top_k=5)

    assert len(ranked) == 1
    assert ranked[0]["chunk_id"] == "lg_01"
    assert ranked[0]["rerank_score"] == pytest.approx(3.1415)


def test_rerank_bypass_when_disabled(sample_vector_chunks):
    ranked = rerank("query", sample_vector_chunks, top_k=2, enabled=False)
    assert len(ranked) == 2
    assert [c["chunk_id"] for c in ranked] == ["lg_01", "fa_01"]
    assert "rerank_score" not in ranked[0]


@patch("generation.reranker._get_reranker")
def test_rerank_falls_back_on_inference_error(mock_get_reranker, sample_vector_chunks):
    mock_get_reranker.side_effect = RuntimeError("Model load failed")

    ranked = rerank("query", sample_vector_chunks, top_k=2)
    assert len(ranked) == 2
    assert [c["chunk_id"] for c in ranked] == ["lg_01", "fa_01"]


def test_rerank_empty_input():
    assert rerank("query", [], top_k=5) == []


# ---------------------------------------------------------------------------
# 3. LangGraph Node (agents/knowledge_retriever.py) Tests
# ---------------------------------------------------------------------------


@patch("agents.knowledge_retriever.rerank")
@patch("agents.knowledge_retriever.retrieve")
def test_knowledge_retriever_run_end_to_end_with_subgraph(
    mock_retrieve, mock_rerank, sample_vector_chunks, monkeypatch
):
    mock_retrieve.return_value = sample_vector_chunks
    mock_rerank.return_value = sample_vector_chunks[:2]

    fake_graph_mod = types.ModuleType("retrieval.graph_retriever")
    fake_graph_mod.retrieve_subgraph = MagicMock(
        return_value={
            "nodes": [{"id": "StateGraph", "label": "StateGraph", "type": "Class"}],
            "edges": [{"source": "StateGraph", "target": "CopilotState", "relation": "USES"}],
        }
    )
    monkeypatch.setitem(sys.modules, "retrieval.graph_retriever", fake_graph_mod)

    state = {
        "question": "How do I wire CopilotState into StateGraph?",
        "top_k": 2,
        "use_graph": True,
        "use_reranker": True,
    }

    output = knowledge_retriever.run(state)

    mock_retrieve.assert_called_once_with(
        "How do I wire CopilotState into StateGraph?", k=15, use_graph=True
    )
    mock_rerank.assert_called_once()
    fake_graph_mod.retrieve_subgraph.assert_called_once_with(
        "How do I wire CopilotState into StateGraph?"
    )

    assert set(output.keys()) == {"chunks", "graph"}
    assert len(output["chunks"]) == 2
    assert len(output["graph"]["nodes"]) == 1
    assert len(output["graph"]["edges"]) == 1


def test_knowledge_retriever_run_empty_question():
    output = knowledge_retriever.run({"question": "   ", "top_k": 5})
    assert output == {"chunks": [], "graph": {"nodes": [], "edges": []}}