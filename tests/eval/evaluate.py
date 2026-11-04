# tests/eval/evaluate.py - Cross-module owner: Aya
#
# Aya runs evaluation because she owns the end-to-end UX
# and needs to validate the full pipeline output.

import json
from retrieval.hybrid_retriever import retrieve
from generation.answer_generator import generate_answer

with open("tests/eval/questions.json") as f:
    QUESTIONS = json.load(f)

def evaluate():
    for q in QUESTIONS:
        print(f"\nQ{q['id']}: {q['question']}")
        chunks = retrieve(q["question"], k=5)
        result = generate_answer(q["question"], chunks)
        print(f"  Answer : {result['answer'][:120]}...")
        print(f"  Sources: {[s['framework'] for s in result['sources']]}")
        print(f"  Expected: {q['expected_framework']}")

if __name__ == "__main__":
    evaluate()
