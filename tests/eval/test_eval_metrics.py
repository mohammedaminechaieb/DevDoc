# tests/eval/test_eval_metrics.py
# Owner: Oussema
# Tests of the scoring code of evaluate.py (pure functions + a fake copilot): no LLM, no network.
import json

from tests.eval import evaluate as ev

Q_CODE = {"id": 9, "category": "code", "expected_intent": "code", "expected_framework": "langgraph",
          "question": "Give me a LangGraph example"}
Q_OOS = {"id": 15, "category": "out_of_scope", "expected_intent": "learn", "expected_framework": None,
         "question": "What is the capital of Mars?", "expect_no_answer": True}
SRC = [{"chunk_id": "c1", "url": "https://x.dev/a", "framework": "langgraph", "text": "..."}]


def good_result():
    return {"intent": "code", "answer": "Use StateGraph [1].", "sources": SRC,
            "review": {"ok": True, "issues": []}}


def test_questions_file_is_valid():
    qs = ev.load_questions()
    assert len(qs) >= 15
    assert len({q["id"] for q in qs}) == len(qs)                               # unique ids
    assert {q["expected_intent"] for q in qs} <= {"learn", "recommend", "design", "code", "explore", "evaluate"}
    for q in qs:
        assert q["question"].strip() and 3 <= len(q["question"]) <= 2000       # API limits (QueryRequest)


def test_load_questions_filters():
    only_code = ev.load_questions(categories=["code"])
    assert only_code and all(q["category"] == "code" for q in only_code)
    assert len(ev.load_questions(limit=2)) == 2


def test_score_result_success():
    row = ev.score_result(Q_CODE, good_result(), 1.234)
    assert row["intent_ok"] and row["framework_ok"] and row["cited"] and row["review_ok"]
    assert row["latency_s"] == 1.23 and row["error"] is None and row["refusal_ok"] is None


def test_score_result_wrong_intent_and_framework():
    result = {**good_result(), "intent": "learn", "sources": [{**SRC[0], "framework": "crewai"}]}
    row = ev.score_result(Q_CODE, result, 0.1)
    assert row["intent_ok"] is False and row["framework_ok"] is False


def test_score_result_error_never_counts_as_success():
    row = ev.score_result(Q_CODE, None, 0.5, error="not implemented: code assistant")
    assert row["intent_ok"] is False and row["framework_ok"] is False and row["review_ok"] is False
    assert row["error"]


def test_crashed_out_of_scope_question_is_not_a_refusal():
    row = ev.score_result(Q_OOS, None, 0.1, error="boom")
    assert row["refusal_ok"] is False


def test_framework_metric_not_applicable_without_expectation():
    q = {**Q_CODE, "expected_framework": None}
    assert ev.score_result(q, good_result(), 0.1)["framework_ok"] is None


def test_citation_detection():
    assert ev.has_citations("see [2]", [])
    assert ev.has_citations("docs at https://x.dev/a", SRC)
    assert not ev.has_citations("no reference at all", SRC)


def test_refusal_detection_on_out_of_scope():
    refused = {"intent": "learn", "answer": "I could not find any relevant passage.", "sources": []}
    invented = {"intent": "learn", "answer": "The capital of Mars is Olympus City.", "sources": SRC}
    assert ev.score_result(Q_OOS, refused, 0.1)["refusal_ok"] is True
    assert ev.score_result(Q_OOS, invented, 0.1)["refusal_ok"] is False


def test_summarize_per_category_and_overall():
    rows = [
        ev.score_result(Q_CODE, good_result(), 1.0),
        ev.score_result(Q_CODE, {**good_result(), "intent": "learn"}, 3.0),
        ev.score_result(Q_OOS, None, 0.0, error="boom"),
    ]
    s = ev.summarize(rows)
    assert list(s)[-1] == "ALL"
    assert s["code"]["n"] == 2 and s["code"]["intent"] == (1, 2) and s["code"]["latency_s"] == 2.0
    assert s["out_of_scope"]["errors"] == 1
    assert s["ALL"]["n"] == 3 and s["ALL"]["errors"] == 1
    assert "category" in ev.format_summary(s) and "ALL" in ev.format_summary(s)


def test_run_evaluation_survives_failures_with_a_fake_copilot():
    def fake(question, top_k=5, use_graph=True):
        if "Mars" in question:
            raise NotImplementedError("llm")
        if "boom" in question:
            raise RuntimeError("neo4j down")
        assert top_k == 3 and use_graph is False
        return good_result()

    qs = [Q_CODE, Q_OOS, {**Q_CODE, "id": 99, "question": "boom?"}]
    rows = ev.run_evaluation(qs, top_k=3, use_graph=False, runner=fake, verbose=False)
    assert [bool(r["error"]) for r in rows] == [False, True, True]
    assert rows[1]["error"].startswith("not implemented") and "neo4j down" in rows[2]["error"]


def test_save_report_writes_json_and_csv(tmp_path):
    rows = [ev.score_result(Q_CODE, good_result(), 1.0)]
    json_path, csv_path = ev.save_report(rows, ev.summarize(rows), tmp_path, tag="t")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["rows"][0]["id"] == 9 and "ALL" in data["summary"]
    assert csv_path.read_text(encoding="utf-8").startswith("id,category")
