# tests/eval/evaluate.py - Cross-module owner: Aya
#
# Runs every question of questions.json through the full copilot and reports
# intent accuracy and framework hit rate per category.
# Run: python -m tests.eval.evaluate

import json
from collections import defaultdict
from pathlib import Path

from agents.orchestrator import run_copilot

QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text(encoding="utf-8"))


def evaluate():
    stats = defaultdict(lambda: {"n": 0, "intent_ok": 0, "fw_n": 0, "fw_ok": 0})
    for q in QUESTIONS:
        r = run_copilot(q["question"], top_k=5)
        frameworks = [s["framework"] for s in r.get("sources", [])]
        s = stats[q["category"]]
        s["n"] += 1
        s["intent_ok"] += r.get("intent") == q["expected_intent"]
        if q["expected_framework"]:
            s["fw_n"] += 1
            s["fw_ok"] += q["expected_framework"] in frameworks
        print(f"\nQ{q['id']} [{q['category']}] {q['question']}")
        print(f"  intent : {r.get('intent')} (expected {q['expected_intent']})")
        print(f"  sources: {frameworks} (expected {q['expected_framework']})")
        print(f"  answer : {r.get('answer', '')[:120]}...")
        print(f"  review : {r.get('review')}")

    print("\n=== Summary ===")
    for cat, s in stats.items():
        fw = f"{s['fw_ok']}/{s['fw_n']}" if s["fw_n"] else "-"
        print(f"{cat:13} intent {s['intent_ok']}/{s['n']}   framework {fw}")


if __name__ == "__main__":
    evaluate()
