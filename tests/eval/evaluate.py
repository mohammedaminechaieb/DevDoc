# tests/eval/evaluate.py
# Owner: Oussema
#
# Runs every question of questions.json through the full copilot and reports, per category:
#   intent accuracy, framework hit rate, share of answers accepted by the reviewer,
#   share of answers that cite their sources, refusal on out-of-scope questions, latency.
# Results are also written to data/eval/ (JSON + CSV) so runs can be compared.
#
# Run (from the repo root):
#   python -m tests.eval.evaluate                       # all questions, hybrid retrieval
#   python -m tests.eval.evaluate --compare             # vector only vs hybrid (GraphRAG)
#   python -m tests.eval.evaluate --category code --limit 3 --top-k 3
#
# The scoring / summary functions are pure (no LLM, no network): see tests/eval/test_eval_metrics.py.

import argparse
import csv
import json
import re
import statistics
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS_PATH = Path(__file__).parent / "questions.json"
DEFAULT_OUT = ROOT / "data" / "eval"          # data/ is git-ignored

# An out-of-scope question should get an honest "I do not know", not an invented answer
REFUSAL_MARKERS = (
    "could not find", "not in the context", "not mentioned", "does not contain", "doesn't contain",
    "no information", "no relevant", "cannot answer", "can't answer", "not covered",
    "does not provide", "do not have", "not provided",
)
_CITATION = re.compile(r"\[\d{1,3}\]")


# --------------------------------------------------------------------------- data
def load_questions(path: Path = QUESTIONS_PATH, categories: list[str] | None = None,
                   limit: int | None = None) -> list[dict]:
    questions = json.loads(Path(path).read_text(encoding="utf-8"))
    if categories:
        questions = [q for q in questions if q["category"] in categories]
    return questions[:limit] if limit else questions


# --------------------------------------------------------------------------- scoring (pure)
def is_refusal(answer: str, sources: list[dict]) -> bool:
    text = (answer or "").lower()
    return not sources or any(marker in text for marker in REFUSAL_MARKERS)


def has_citations(answer: str, sources: list[dict]) -> bool:
    """True if the answer cites a source inline ([1]) or by URL."""
    if _CITATION.search(answer or ""):
        return True
    return any(s.get("url") and s["url"] in (answer or "") for s in sources)


def score_result(question: dict, result: dict | None, latency: float, error: str | None = None) -> dict:
    """One row of the report for one question."""
    result = result or {}
    sources = result.get("sources") or []
    answer = result.get("answer") or ""
    frameworks = [s.get("framework") for s in sources]
    expected_fw = question.get("expected_framework")
    review = result.get("review") or {}
    row = {
        "id": question["id"],
        "category": question["category"],
        "question": question["question"],
        "expected_intent": question["expected_intent"],
        "intent": result.get("intent"),
        "intent_ok": result.get("intent") == question["expected_intent"],
        "expected_framework": expected_fw,
        "frameworks": frameworks,
        "framework_ok": (expected_fw in frameworks) if expected_fw else None,
        "n_sources": len(sources),
        "cited": has_citations(answer, sources) if answer and sources else False,
        "review_ok": review.get("ok") if review else None,
        "review_issues": review.get("issues", []),
        "refusal_ok": is_refusal(answer, sources) if question.get("expect_no_answer") else None,
        "answer": answer,
        "latency_s": round(latency, 2),
        "error": error,
    }
    if error:                                  # a crashed question never counts as a success
        row["intent_ok"] = False
        row["framework_ok"] = False if expected_fw else None
        row["review_ok"] = False
        row["refusal_ok"] = False if question.get("expect_no_answer") else None
    return row


def _rate(values: list[bool | None]) -> tuple[int, int]:
    """(successes, total) ignoring the None entries (metric not applicable)."""
    applicable = [v for v in values if v is not None]
    return sum(bool(v) for v in applicable), len(applicable)


def summarize(rows: list[dict]) -> dict:
    """Aggregate rows per category and overall: {category: {metric: (ok, total) | float}}."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["category"]].append(r)
        groups["ALL"].append(r)

    out = {}
    for cat, rs in groups.items():
        answered = [r for r in rs if not r["error"]]
        out[cat] = {
            "n": len(rs),
            "errors": len(rs) - len(answered),
            "intent": _rate([r["intent_ok"] for r in rs]),
            "framework": _rate([r["framework_ok"] for r in rs]),
            "review_ok": _rate([r["review_ok"] for r in rs]),
            "cited": _rate([r["cited"] for r in answered]),
            "refusal": _rate([r["refusal_ok"] for r in rs]),
            "latency_s": round(statistics.mean(r["latency_s"] for r in rs), 2) if rs else 0.0,
        }
    return dict(sorted(out.items(), key=lambda kv: (kv[0] == "ALL", kv[0])))


def format_summary(summary: dict, title: str = "Summary") -> str:
    def cell(rate):
        ok, total = rate
        return f"{ok}/{total}" if total else "-"

    head = f"{'category':13} {'n':>3} {'intent':>7} {'framework':>10} {'review':>7} {'cited':>7} {'refusal':>8} {'err':>4} {'avg s':>6}"
    lines = [f"=== {title} ===", head, "-" * len(head)]
    for cat, s in summary.items():
        lines.append(
            f"{cat:13} {s['n']:>3} {cell(s['intent']):>7} {cell(s['framework']):>10} "
            f"{cell(s['review_ok']):>7} {cell(s['cited']):>7} {cell(s['refusal']):>8} "
            f"{s['errors']:>4} {s['latency_s']:>6}"
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- running
def _default_runner() -> Callable[..., dict]:
    from agents.orchestrator import run_copilot       # imported late: heavy (LangGraph, models)
    return run_copilot


def run_evaluation(questions: list[dict], top_k: int = 5, use_graph: bool = True,
                   runner: Callable[..., dict] | None = None, verbose: bool = True) -> list[dict]:
    runner = runner or _default_runner()
    rows = []
    for q in questions:
        start = time.perf_counter()
        result, error = None, None
        try:
            result = runner(q["question"], top_k=top_k, use_graph=use_graph)
        except NotImplementedError as e:
            error = f"not implemented: {e}" if str(e) else "not implemented"
        except Exception as e:                        # noqa: BLE001 - one bad question must not stop the run
            error = f"{type(e).__name__}: {e}"
        row = score_result(q, result, time.perf_counter() - start, error)
        rows.append(row)
        if verbose:
            print_row(row)
    return rows


def print_row(r: dict) -> None:
    print(f"\nQ{r['id']} [{r['category']}] {r['question']}")
    if r["error"]:
        print(f"  ERROR  : {r['error']}")
        return
    print(f"  intent : {r['intent']} (expected {r['expected_intent']})")
    print(f"  sources: {r['frameworks']} (expected {r['expected_framework']})")
    print(f"  answer : {r['answer'][:120]}...")
    print(f"  review : ok={r['review_ok']} {r['review_issues'] or ''}   cited={r['cited']}   {r['latency_s']}s")


# --------------------------------------------------------------------------- report files
def save_report(rows: list[dict], summary: dict, out_dir: Path = DEFAULT_OUT, tag: str = "run") -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = out_dir / f"eval-{tag}-{stamp}.json"
    csv_path = out_dir / f"eval-{tag}-{stamp}.csv"
    json_path.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    flat = [{**r, "frameworks": ",".join(map(str, r["frameworks"])),
             "review_issues": " | ".join(r["review_issues"]), "answer": r["answer"][:300]} for r in rows]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(flat[0]) if flat else ["id"])
        writer.writeheader()
        writer.writerows(flat)
    return json_path, csv_path


def evaluate(top_k: int = 5, use_graph: bool = True, categories: list[str] | None = None,
             limit: int | None = None, out_dir: Path | None = DEFAULT_OUT, tag: str = "run",
             runner: Callable[..., dict] | None = None, verbose: bool = True) -> tuple[list[dict], dict]:
    """Programmatic entry point (used by notebooks/04_evaluation.ipynb)."""
    rows = run_evaluation(load_questions(categories=categories, limit=limit), top_k, use_graph, runner, verbose)
    summary = summarize(rows)
    if verbose:
        print("\n" + format_summary(summary, title=f"Summary ({tag})"))
    if out_dir and rows:
        json_path, _ = save_report(rows, summary, out_dir, tag)
        if verbose:
            print(f"\nReport saved to {json_path}")
    return rows, summary


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Evaluate the Agentic AI Copilot on questions.json")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--no-graph", action="store_true", help="vector search only (no Neo4j)")
    p.add_argument("--compare", action="store_true", help="run vector-only AND hybrid and compare")
    p.add_argument("--category", action="append", help="only this category (repeatable)")
    p.add_argument("--limit", type=int, help="only the first N questions")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="report folder (default: data/eval)")
    args = p.parse_args(argv)

    if args.compare:
        for label, graph in (("vector", False), ("hybrid", True)):
            print(f"\n######## {label} retrieval (use_graph={graph}) ########")
            evaluate(args.top_k, graph, args.category, args.limit, args.out, tag=label)
    else:
        evaluate(args.top_k, not args.no_graph, args.category, args.limit, args.out,
                 tag="vector" if args.no_graph else "hybrid")


if __name__ == "__main__":
    main()
