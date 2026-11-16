# agents/evaluation_assistant.py
# Owner: Oussema
# Role: Evaluation Assistant
#   run()    - answers feature F questions (evaluation, reliability, hallucinations)
#   review() - checks every answer before it is returned (grounding, citations)
#
# review() is deterministic (no LLM call, no network) so it can run on every request:
#   1. the answer is not empty and comes with sources
#   2. inline citations [n] point to an existing source
#   3. URLs written in the answer come from the retrieved sources (no invented links)
#   4. the vocabulary of the answer is supported by the retrieved passages (grounding)
# An LLM-as-a-judge pass can be added with REVIEW_USE_LLM=1 (off by default: it doubles latency).

import json
import logging
import os
import re

from agents.state import CopilotState
from generation.llm_client import call_llm
from generation.prompt_builder import SYSTEM_PROMPT, build_prompt

log = logging.getLogger(__name__)

INSTRUCTIONS = (
    "Explain how to evaluate and improve the user's agentic system: answer quality, tool "
    "usage, execution errors, hallucination mitigation, reliability and performance of "
    "multi-agent systems. Cite the sources."
)

NO_CONTEXT_ANSWER = (
    "I could not find any relevant passage in the documentation to answer this question."
)

# Review thresholds
MIN_GROUNDING = 0.35     # below this share of supported words, the answer is flagged
MIN_WORDS_FOR_GROUNDING = 15   # shorter answers are too small to measure
MIN_WORDS_FOR_CITATION = 30    # a one-line answer does not need inline citations
JUDGE_MAX_CHUNKS = 6
JUDGE_MAX_CHARS = 800

_STOPWORDS = set(
    """this that these those with from into over under about above below between through during
    their there which while where when what will would could should have has had been being
    were are was does did doing done also such than then them they your you its it's can may might
    must not but and for the use used using uses each other more most some any all only very just
    like make makes made based within without across per via one two three first second""".split()
)

_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_URL = re.compile(r"(?:https?|file)://[^\s)\]>\"'`]+")
_CITATION = re.compile(r"\[(\d{1,3})\]")
_SOURCES_TAIL = re.compile(r"\n[ \t#*_]*sources?[ \t*_]*:?[ \t*_]*\n.*\Z", re.IGNORECASE | re.DOTALL)


# --------------------------------------------------------------------------- feature F
def _format_sources(chunks: list[dict]) -> list[dict]:
    """Same shape as the other agents: only the fields the API and the frontend need.
    The order is kept, so the inline numbers [n] of the prompt match the sources list."""
    return [
        {
            "chunk_id": c.get("chunk_id"),
            "url": c.get("url"),
            "framework": c.get("framework"),
            "text": c.get("text"),
        }
        for c in chunks
    ]


def run(state: CopilotState) -> dict:
    """Feature F: grounded answer about evaluating / securing / optimising an agentic system."""
    chunks = state.get("chunks", [])
    if not chunks:
        return {"answer": NO_CONTEXT_ANSWER, "sources": []}

    prompt = build_prompt(state["question"], chunks, INSTRUCTIONS)
    answer = call_llm(prompt, system=SYSTEM_PROMPT)
    return {"answer": answer, "sources": _format_sources(chunks)}


# --------------------------------------------------------------------------- reviewer
def is_no_context_answer(answer: str) -> bool:
    """True for the honest 'nothing found' answer: it needs no sources."""
    return answer.strip().lower().startswith("i could not find any relevant passage")


def _prose(answer: str) -> str:
    """Answer text without code, the trailing 'Sources' list, URLs and [n] markers."""
    text = _FENCE.sub(" ", answer)
    text = _INLINE_CODE.sub(" ", text)
    text = _SOURCES_TAIL.sub("", text)
    text = _URL.sub(" ", text)
    return _CITATION.sub(" ", text)


def _words(text: str) -> set[str]:
    words = set()
    for w in re.findall(r"[a-z][a-z0-9_]{3,}", text.lower()):
        if w in _STOPWORDS:
            continue
        words.add(w[:-1] if w.endswith("s") and len(w) > 4 else w)
    return words


def grounding_score(answer: str, context: str) -> float | None:
    """Share of the answer's content words that also appear in the retrieved passages.
    None when the answer is too short (or the context empty) to be measured."""
    answer_words = _words(_prose(answer))
    context_words = _words(context)
    if len(answer_words) < MIN_WORDS_FOR_GROUNDING or not context_words:
        return None
    return len(answer_words & context_words) / len(answer_words)


def _norm_url(url: str) -> str:
    return url.split("#", 1)[0].rstrip("/").rstrip(".,;:").lower()


def check_answer(answer: str, sources: list[dict], chunks: list[dict] | None = None) -> list[str]:
    """Deterministic checks. Returns the list of problems found (empty = the answer looks sound)."""
    answer = (answer or "").strip()
    if not answer:
        return ["the answer is empty"]
    if is_no_context_answer(answer):
        return []

    issues: list[str] = []
    if not sources:
        issues.append("answer has no supporting sources")

    # inline citations [n]
    prose_with_markers = _INLINE_CODE.sub(" ", _FENCE.sub(" ", answer))
    cited = {int(n) for n in _CITATION.findall(prose_with_markers)}
    known = {_norm_url(s["url"]) for s in sources if s.get("url")}
    known |= {_norm_url(c["url"]) for c in (chunks or []) if c.get("url")}
    urls_in_answer = {_norm_url(u) for u in _URL.findall(_FENCE.sub(" ", answer))}
    long_enough = len(re.findall(r"\w+", _prose(answer))) >= MIN_WORDS_FOR_CITATION
    if sources and long_enough and not cited and not (urls_in_answer & known):
        issues.append("the answer does not cite its sources (inline [1], [2]... or source URLs)")
    out_of_range = sorted(n for n in cited if n < 1 or n > len(sources))
    if out_of_range:
        shown = ", ".join(f"[{n}]" for n in out_of_range[:5])
        issues.append(f"cites {shown} but only {len(sources)} source(s) were provided")

    # URLs must come from the retrieved passages
    unknown = []
    for url in _URL.findall(_FENCE.sub(" ", answer)):
        if _norm_url(url) not in known and url not in unknown:
            unknown.append(url)
    if unknown:
        issues.append("mentions URL(s) that are not in the retrieved sources: " + ", ".join(unknown[:3]))

    # grounding of the vocabulary
    context = " ".join(c.get("text") or "" for c in (chunks or sources))
    score = grounding_score(answer, context)
    if score is not None and score < MIN_GROUNDING:
        issues.append(
            f"low overlap with the retrieved passages ({score:.0%} of the answer's terms): "
            "possible hallucination"
        )
    return issues


# --------------------------------------------------------------------------- optional LLM judge
JUDGE_PROMPT = """You verify answers produced by a documentation assistant.

CONTEXT (the only allowed knowledge):
{context}

QUESTION: {question}

ANSWER TO VERIFY:
{answer}

List every claim of the answer that is NOT supported by the context.
Reply with ONLY a JSON object, no explanation:
{{"supported": true or false, "issues": ["<unsupported claim>", ...]}}"""


def _judge(question: str, answer: str, chunks: list[dict]) -> list[str]:
    """LLM-as-a-judge. Never raises: a failing judge must not break the request."""
    context = "\n\n".join(
        f"[{i}] {(c.get('text') or '')[:JUDGE_MAX_CHARS]}"
        for i, c in enumerate(chunks[:JUDGE_MAX_CHUNKS], start=1)
    )
    prompt = JUDGE_PROMPT.format(context=context or "(none)", question=question, answer=answer[:3000])
    try:
        raw = call_llm(prompt, system="You are a strict fact checker that replies with JSON only.")
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0)) if match else {}
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM judge unavailable (%s: %s)", type(exc).__name__, exc)
        return []
    if data.get("supported") is not False:
        return []
    claims = [str(i)[:200] for i in data.get("issues", []) if i][:3]
    return [f"judge: {c}" for c in claims] or ["judge: the answer is not fully supported by the context"]


def _judge_enabled() -> bool:
    return os.getenv("REVIEW_USE_LLM", "").strip().lower() in ("1", "true", "yes")


def review(state: CopilotState) -> dict:
    """Last node of the graph: verifies the answer before it is returned to the user.
    Returns {"review": {"ok": bool, "issues": [str]}}."""
    try:
        answer = state.get("answer") or ""
        sources = state.get("sources") or []
        chunks = state.get("chunks") or []
        issues = check_answer(answer, sources, chunks)
        if _judge_enabled() and answer.strip() and not is_no_context_answer(answer):
            issues += _judge(state.get("question", ""), answer, chunks or sources)
    except Exception as exc:  # noqa: BLE001 - the reviewer must never break the pipeline
        log.exception("review failed")
        return {"review": {"ok": False, "issues": [f"review could not be completed: {type(exc).__name__}"]}}
    return {"review": {"ok": not issues, "issues": issues}}
