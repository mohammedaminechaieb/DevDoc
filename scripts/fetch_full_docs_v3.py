#!/usr/bin/env python3
"""
fetch_full_docs_v3.py — Agentic AI Copilot corpus builder
==========================================================
Builds full_corpus/full_corpus_clean.jsonl from:
  - HTTP-fetched docs: LangGraph, OpenAI, Anthropic, Foundational papers
  - Local file docs:   LangChain, CrewAI, AutoGen, MCP  (from raw_docs/)

Usage
-----
  python scripts/fetch_full_docs_v3.py                    # fetch + chunk everything
  python scripts/fetch_full_docs_v3.py --chunk-only       # skip HTTP, re-chunk raw_docs only
  python scripts/fetch_full_docs_v3.py --framework X      # one framework only (incremental)

Frameworks: langgraph, langchain, crewai, autogen, mcp, openai, anthropic, foundational
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CHUNK_SIZE    = 150   # words
CHUNK_OVERLAP = 30
MIN_WORDS     = 20
OUTPUT_DIR    = Path("full_corpus")
RAW_DOCS_DIR  = Path("raw_docs")
CORPUS_FILE   = OUTPUT_DIR / "full_corpus_clean.jsonl"
ZIP_FILE      = OUTPUT_DIR / "full_corpus_agentic_ai.zip"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AgenticAI-Corpus-Builder/3.0)"
}
REQUEST_DELAY = 1.2   # seconds between HTTP requests
REQUEST_TIMEOUT = 30

# ---------------------------------------------------------------------------
# SOURCES — all 8 frameworks
# LangGraph, OpenAI, Anthropic, Foundational: HTTP fetch
# LangChain, CrewAI, AutoGen, MCP: local raw_docs/ files
# ---------------------------------------------------------------------------
SOURCES = [
    # ------------------------------------------------------------------ LangGraph (HTTP)
    {
        "framework": "langgraph",
        "method": "http_pages",
        "version": "0.2",
        "pages": [
            ("add_memory",          "https://docs.langchain.com/oss/python/langgraph/add-memory.md"),
            ("agentic_rag",         "https://docs.langchain.com/oss/python/langgraph/agentic-rag.md"),
            ("application_structure","https://docs.langchain.com/oss/python/langgraph/application-structure.md"),
            ("backward_compat",     "https://docs.langchain.com/oss/python/langgraph/backward-compatibility.md"),
            ("case_studies",        "https://docs.langchain.com/oss/python/langgraph/case-studies.md"),
            ("changelog_py",        "https://docs.langchain.com/oss/python/langgraph/changelog-py.md"),
            ("checkpointers",       "https://docs.langchain.com/oss/python/langgraph/checkpointers.md"),
            ("choosing_apis",       "https://docs.langchain.com/oss/python/langgraph/choosing-apis.md"),
            ("deploy",              "https://docs.langchain.com/oss/python/langgraph/deploy.md"),
            ("error_graph_recursion","https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT.md"),
            ("error_invalid_chat",  "https://docs.langchain.com/oss/python/langgraph/errors/INVALID_CHAT_HISTORY.md"),
            ("error_concurrent",    "https://docs.langchain.com/oss/python/langgraph/errors/INVALID_CONCURRENT_GRAPH_UPDATE.md"),
            ("error_node_return",   "https://docs.langchain.com/oss/python/langgraph/errors/INVALID_GRAPH_NODE_RETURN_VALUE.md"),
            ("error_missing_ckpt",  "https://docs.langchain.com/oss/python/langgraph/errors/MISSING_CHECKPOINTER.md"),
            ("error_multi_subgraph","https://docs.langchain.com/oss/python/langgraph/errors/MULTIPLE_SUBGRAPHS.md"),
            ("event_streaming",     "https://docs.langchain.com/oss/python/langgraph/event-streaming.md"),
            ("fault_tolerance",     "https://docs.langchain.com/oss/python/langgraph/fault-tolerance.md"),
            ("functional_api",      "https://docs.langchain.com/oss/python/langgraph/functional-api.md"),
            ("graph_api",           "https://docs.langchain.com/oss/python/langgraph/graph-api.md"),
            ("install",             "https://docs.langchain.com/oss/python/langgraph/install.md"),
            ("interrupts",          "https://docs.langchain.com/oss/python/langgraph/interrupts.md"),
            ("local_server",        "https://docs.langchain.com/oss/python/langgraph/local-server.md"),
            ("observability",       "https://docs.langchain.com/oss/python/langgraph/observability.md"),
            ("overview",            "https://docs.langchain.com/oss/python/langgraph/overview.md"),
            ("persistence",         "https://docs.langchain.com/oss/python/langgraph/persistence.md"),
            ("pregel",              "https://docs.langchain.com/oss/python/langgraph/pregel.md"),
            ("quickstart",          "https://docs.langchain.com/oss/python/langgraph/quickstart.md"),
            ("sql_agent",           "https://docs.langchain.com/oss/python/langgraph/sql-agent.md"),
            ("stores",              "https://docs.langchain.com/oss/python/langgraph/stores.md"),
            ("streaming",           "https://docs.langchain.com/oss/python/langgraph/streaming.md"),
            ("thinking",            "https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph.md"),
            ("use_functional_api",  "https://docs.langchain.com/oss/python/langgraph/use-functional-api.md"),
            ("use_graph_api",       "https://docs.langchain.com/oss/python/langgraph/use-graph-api.md"),
            ("use_subgraphs",       "https://docs.langchain.com/oss/python/langgraph/use-subgraphs.md"),
            ("use_time_travel",     "https://docs.langchain.com/oss/python/langgraph/use-time-travel.md"),
            ("workflows_agents",    "https://docs.langchain.com/oss/python/langgraph/workflows-agents.md"),
            ("durable_execution",   "https://docs.langchain.com/oss/python/langgraph/durable-execution.md"),
            ("memory_concept",      "https://docs.langchain.com/oss/python/langgraph/memory.md"),
            ("studio",              "https://docs.langchain.com/oss/python/langgraph/studio.md"),
            ("test",                "https://docs.langchain.com/oss/python/langgraph/test.md"),
            ("ui",                  "https://docs.langchain.com/oss/python/langgraph/ui.md"),
            ("frontend_overview",   "https://docs.langchain.com/oss/python/langgraph/frontend/overview.md"),
            ("graph_execution",     "https://docs.langchain.com/oss/python/langgraph/frontend/graph-execution.md"),
            ("custom_stream",       "https://docs.langchain.com/oss/python/langgraph/frontend/custom-stream-channels.md"),
        ],
    },

    # ------------------------------------------------------------------ OpenAI (HTTP)
    {
        "framework": "openai",
        "method": "http_pages",
        "version": "2024",
        "pages": [
            ("overview",            "https://platform.openai.com/docs/overview"),
            ("models",              "https://platform.openai.com/docs/models"),
            ("function_calling",    "https://platform.openai.com/docs/guides/function-calling"),
            ("structured_outputs",  "https://platform.openai.com/docs/guides/structured-outputs"),
            ("tool_calling",        "https://platform.openai.com/docs/guides/tool-calling"),
            ("agents",              "https://platform.openai.com/docs/guides/agents"),
            ("responses_api",       "https://platform.openai.com/docs/guides/responses"),
            ("reasoning",           "https://platform.openai.com/docs/guides/reasoning"),
            ("chat_completions",    "https://platform.openai.com/docs/guides/chat-completions"),
            ("text_generation",     "https://platform.openai.com/docs/guides/text-generation"),
            ("embeddings",          "https://platform.openai.com/docs/guides/embeddings"),
            ("fine_tuning",         "https://platform.openai.com/docs/guides/fine-tuning"),
            ("batch",               "https://platform.openai.com/docs/guides/batch"),
            ("files",               "https://platform.openai.com/docs/guides/files"),
            ("images",              "https://platform.openai.com/docs/guides/images"),
            ("audio",               "https://platform.openai.com/docs/guides/audio"),
            ("realtime",            "https://platform.openai.com/docs/guides/realtime"),
            ("moderation",          "https://platform.openai.com/docs/guides/moderation"),
            ("rate_limits",         "https://platform.openai.com/docs/guides/rate-limits"),
            ("error_codes",         "https://platform.openai.com/docs/guides/error-codes"),
            ("prompt_engineering",  "https://platform.openai.com/docs/guides/prompt-engineering"),
            ("production_best_practices", "https://platform.openai.com/docs/guides/production-best-practices"),
            ("safety",              "https://platform.openai.com/docs/guides/safety-best-practices"),
            ("latency",             "https://platform.openai.com/docs/guides/latency-optimization"),
            ("assistants",          "https://platform.openai.com/docs/assistants/overview"),
            ("assistants_tools",    "https://platform.openai.com/docs/assistants/tools"),
            ("assistants_streaming","https://platform.openai.com/docs/assistants/streaming"),
            ("vector_stores",       "https://platform.openai.com/docs/assistants/tools/file-search/vector-stores"),
            ("code_interpreter",    "https://platform.openai.com/docs/assistants/tools/code-interpreter"),
            ("completions_legacy",  "https://platform.openai.com/docs/guides/completions"),
            ("libraries",           "https://platform.openai.com/docs/libraries"),
        ],
    },

    # ------------------------------------------------------------------ Anthropic (HTTP)
    {
        "framework": "anthropic",
        "method": "http_pages",
        "version": "2024",
        "pages": [
            ("tool_use",            "https://docs.anthropic.com/en/docs/build-with-claude/tool-use"),
            ("tool_use_overview",   "https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview"),
            ("tool_use_implement",  "https://docs.anthropic.com/en/docs/build-with-claude/tool-use/implement-tool-use"),
            ("tool_use_client_tools","https://docs.anthropic.com/en/docs/build-with-claude/tool-use/client-side-tools"),
            ("tool_use_computer",   "https://docs.anthropic.com/en/docs/build-with-claude/tool-use/computer-use"),
            ("agents_overview",     "https://docs.anthropic.com/en/docs/build-with-claude/agents-and-agentic-tasks"),
            ("agents_orchestration","https://docs.anthropic.com/en/docs/build-with-claude/orchestration-and-delegation"),
            ("agents_memory",       "https://docs.anthropic.com/en/docs/build-with-claude/memory"),
            ("mcp",                 "https://docs.anthropic.com/en/docs/build-with-claude/mcp"),
            ("models",              "https://docs.anthropic.com/en/docs/about-claude/models"),
            ("models_overview",     "https://docs.anthropic.com/en/docs/about-claude/models/overview"),
            ("prompt_caching",      "https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching"),
            ("extended_thinking",   "https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking"),
            ("streaming",           "https://docs.anthropic.com/en/docs/build-with-claude/streaming"),
            ("vision",              "https://docs.anthropic.com/en/docs/build-with-claude/vision"),
            ("files",               "https://docs.anthropic.com/en/docs/build-with-claude/files"),
            ("embeddings",          "https://docs.anthropic.com/en/docs/build-with-claude/embeddings"),
            ("batch",               "https://docs.anthropic.com/en/docs/build-with-claude/message-batches"),
            ("context_window",      "https://docs.anthropic.com/en/docs/build-with-claude/context-windows"),
            ("rate_limits",         "https://docs.anthropic.com/en/docs/about-claude/rate-limits"),
            ("errors",              "https://docs.anthropic.com/en/docs/build-with-claude/error-handling"),
            ("messages_api",        "https://docs.anthropic.com/en/api/messages"),
            ("prompt_engineering",  "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview"),
            ("chain_of_thought",    "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-of-thought"),
            ("system_prompts",      "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts"),
            ("multimodal",          "https://docs.anthropic.com/en/docs/build-with-claude/multimodal"),
            ("summarization",       "https://docs.anthropic.com/en/docs/build-with-claude/summarization"),
            ("classifications",     "https://docs.anthropic.com/en/docs/build-with-claude/classify"),
            ("moderation",          "https://docs.anthropic.com/en/docs/about-claude/safety"),
            ("sdk_python",          "https://docs.anthropic.com/en/api/client-sdks"),
            ("getting_started",     "https://docs.anthropic.com/en/docs/get-started"),
            ("intro",               "https://docs.anthropic.com/en/docs/intro"),
        ],
    },

    # ------------------------------------------------------------------ Foundational papers (HTTP)
    {
        "framework": "foundational",
        "method": "http_pages",
        "version": "2022-2024",
        "pages": [
            ("react_paper",         "https://react-lm.github.io/"),
            ("toolformer",          "https://arxiv.org/abs/2302.04761"),
            ("auto_gpt_arxiv",      "https://arxiv.org/abs/2306.02224"),
            ("cognitive_arch",      "https://arxiv.org/abs/2309.02427"),
            ("voyager",             "https://arxiv.org/abs/2305.16291"),
            ("generative_agents",   "https://arxiv.org/abs/2304.03442"),
            ("agentbench",          "https://arxiv.org/abs/2308.03688"),
            ("tool_learning",       "https://arxiv.org/abs/2304.08354"),
            ("hugginggpt",          "https://arxiv.org/abs/2303.17580"),
            ("gorilla",             "https://arxiv.org/abs/2305.15334"),
            ("chain_of_thought",    "https://arxiv.org/abs/2201.11903"),
            ("self_consistency",    "https://arxiv.org/abs/2203.11171"),
            ("tot_paper",           "https://arxiv.org/abs/2305.10601"),
            ("reflexion",           "https://arxiv.org/abs/2303.11366"),
            ("self_refine",         "https://arxiv.org/abs/2303.17651"),
            ("critic",              "https://arxiv.org/abs/2305.11738"),
            ("autogen_paper",       "https://arxiv.org/abs/2308.08155"),
            ("metagpt",             "https://arxiv.org/abs/2308.00352"),
            ("chatdev",             "https://arxiv.org/abs/2307.07924"),
            ("plan_and_solve",      "https://arxiv.org/abs/2305.04091"),
            ("got_paper",           "https://arxiv.org/abs/2308.09687"),
            ("lats",                "https://arxiv.org/abs/2310.04406"),
            ("agentless",           "https://arxiv.org/abs/2407.01489"),
        ],
    },

    # ------------------------------------------------------------------ LangChain (local files)
    {
        "framework": "langchain",
        "method": "local_files",
        "version": "0.3",
        "raw_docs_path": "langchain",
        "extensions": [".md", ".mdx", ".rst", ".txt"],
    },

    # ------------------------------------------------------------------ CrewAI (local files)
    {
        "framework": "crewai",
        "method": "local_files",
        "version": "1.15.35",
        "raw_docs_path": "crewai",
        "extensions": [".md", ".mdx", ".rst", ".txt"],
    },

    # ------------------------------------------------------------------ AutoGen (local files)
    {
        "framework": "autogen",
        "method": "local_files",
        "version": "0.4",
        "raw_docs_path": "autogen",
        "extensions": [".md", ".mdx", ".rst", ".txt"],
    },

    # ------------------------------------------------------------------ MCP (local files)
    {
        "framework": "mcp",
        "method": "local_files",
        "version": "2024-11",
        "raw_docs_path": "mcp",
        "extensions": [".md", ".mdx", ".rst", ".txt"],
    },
]

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"```[\s\S]*?```", " [CODE_BLOCK] ", text)
    text = re.sub(r"`[^`\n]{1,120}`", " [INLINE_CODE] ", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|[^\n]+\|", " ", text)
    text = re.sub(r"[-=]{3,}", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"https?://\S+", " [URL] ", text)
    text = re.sub(r"[^\w\s\.\,\!\?\:\;\'\"\(\)\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has_code(text: str) -> bool:
    return bool(re.search(r"```|`[^`\n]{3,}`|\bdef \b|\bclass \b|\bimport \b", text))


def detect_language(text: str) -> str:
    if re.search(r"```python|def |import |class ", text):
        return "python"
    if re.search(r"```javascript|```typescript|const |let |function |=>", text):
        return "javascript"
    return "en"


def quality_score(text: str, word_count: int) -> float:
    score = 0.5
    if word_count >= 50:
        score += 0.2
    if word_count >= 100:
        score += 0.1
    if re.search(r"\b(agent|tool|function|model|api|workflow|chain)\b", text, re.I):
        score += 0.1
    if re.search(r"\b(example|usage|how to|step)\b", text, re.I):
        score += 0.1
    return min(score, 1.0)


def dedup_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def chunk_text(text: str, source_id: str, url: str, framework: str,
               concept: str, component: str, version: str):
    words = text.split()
    chunks = []
    start = 0
    chunk_idx = 0
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk_words = words[start:end]
        if len(chunk_words) < MIN_WORDS:
            break
        chunk_text_str = " ".join(chunk_words)
        cleaned = clean_text(chunk_text_str)
        wc = len(cleaned.split())
        if wc >= MIN_WORDS:
            chunks.append({
                "chunk_id":     f"{source_id}_chunk_{chunk_idx:04d}",
                "source_id":    source_id,
                "url":          url,
                "framework":    framework,
                "concept":      concept,
                "component":    component,
                "version":      version,
                "char_start":   sum(len(w) + 1 for w in words[:start]),
                "text":         cleaned,
                "word_count":   wc,
                "char_count":   len(cleaned),
                "has_code":     has_code(chunk_text_str),
                "language":     detect_language(chunk_text_str),
                "quality_score": quality_score(cleaned, wc),
                "dedup_hash":   dedup_hash(cleaned),
                "cleaned":      True,
            })
            chunk_idx += 1
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ---------------------------------------------------------------------------
# HTTP fetching
# ---------------------------------------------------------------------------
def fetch_page(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        # Markdown served directly (docs.langchain.com *.md URLs)
        if "text/plain" in content_type or url.endswith(".md"):
            return resp.text
        # HTML page — extract main content
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer",
                          "aside", "form", "iframe"]):
            tag.decompose()
        main = (soup.find("main") or soup.find("article") or
                soup.find("div", class_=re.compile(r"content|main|docs", re.I)) or
                soup.find("body"))
        return main.get_text(separator="\n") if main else soup.get_text(separator="\n")
    except Exception as e:
        print(f"  [WARN] fetch failed for {url}: {e}")
        return ""


def process_http_source(source: dict) -> list:
    chunks = []
    fw = source["framework"]
    version = source["version"]
    pages = source["pages"]
    print(f"\n[HTTP] {fw} ({len(pages)} pages)")
    for concept, url in pages:
        print(f"  → {concept}: {url}")
        text = fetch_page(url)
        if not text.strip():
            print(f"    [SKIP] empty")
            time.sleep(REQUEST_DELAY)
            continue
        source_id = f"{fw}_{concept}"
        component = concept.split("_")[0]
        page_chunks = chunk_text(text, source_id, url, fw, concept, component, version)
        print(f"    {len(page_chunks)} chunks")
        chunks.extend(page_chunks)
        time.sleep(REQUEST_DELAY)
    return chunks


# ---------------------------------------------------------------------------
# Local file processing
# ---------------------------------------------------------------------------
def read_file_text(filepath: Path) -> str:
    try:
        return filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [WARN] cannot read {filepath}: {e}")
        return ""


def process_local_source(source: dict) -> list:
    chunks = []
    fw = source["framework"]
    version = source["version"]
    raw_path = RAW_DOCS_DIR / source["raw_docs_path"]
    extensions = set(source.get("extensions", [".md", ".mdx"]))

    if not raw_path.exists():
        print(f"\n[LOCAL] {fw}: directory not found: {raw_path} — skipping")
        return []

    files = [f for f in raw_path.rglob("*") if f.is_file() and f.suffix in extensions]
    print(f"\n[LOCAL] {fw}: {len(files)} files in {raw_path}")

    for filepath in sorted(files):
        text = read_file_text(filepath)
        if not text.strip():
            continue
        rel = filepath.relative_to(raw_path)
        parts = list(rel.parts)
        concept   = filepath.stem.replace("-", "_").replace(" ", "_")
        component = parts[0] if len(parts) > 1 else concept
        source_id = f"{fw}_{rel.as_posix().replace('/', '_').replace('.', '_')}"
        url       = f"file://raw_docs/{source['raw_docs_path']}/{rel.as_posix()}"
        file_chunks = chunk_text(text, source_id, url, fw, concept, component, version)
        chunks.extend(file_chunks)

    print(f"  → {len(chunks)} chunks total")
    return chunks


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------
def deduplicate(chunks: list) -> list:
    seen = set()
    result = []
    for c in chunks:
        h = c["dedup_hash"]
        if h not in seen:
            seen.add(h)
            result.append(c)
    return result


# ---------------------------------------------------------------------------
# Save corpus
# ---------------------------------------------------------------------------
def save_corpus(chunks: list, existing_path: Path = None) -> int:
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load existing chunks from other frameworks if doing incremental update
    all_chunks = []
    if existing_path and existing_path.exists():
        with open(existing_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    all_chunks.append(json.loads(line))

    all_chunks.extend(chunks)
    all_chunks = deduplicate(all_chunks)

    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # Create zip
    with zipfile.ZipFile(ZIP_FILE, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(CORPUS_FILE, CORPUS_FILE.name)

    print(f"\n✓ Corpus: {len(all_chunks)} chunks → {CORPUS_FILE}")
    print(f"✓ Zip:    {ZIP_FILE}")
    return len(all_chunks)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Build Agentic AI corpus")
    parser.add_argument("--chunk-only", action="store_true",
                        help="Skip HTTP fetching; re-chunk existing raw_docs/ only")
    parser.add_argument("--framework", metavar="FW",
                        help="Process one framework only (incremental mode)")
    args = parser.parse_args()

    target_fw = args.framework.lower() if args.framework else None
    chunk_only = args.chunk_only

    if target_fw:
        valid = {s["framework"] for s in SOURCES}
        if target_fw not in valid:
            print(f"[ERROR] unknown framework '{target_fw}'. Valid: {sorted(valid)}")
            sys.exit(1)

    all_new_chunks = []

    for source in SOURCES:
        fw = source["framework"]
        if target_fw and fw != target_fw:
            continue

        method = source["method"]
        if method == "http_pages":
            if chunk_only:
                print(f"[SKIP] {fw} (HTTP source, --chunk-only mode)")
                continue
            chunks = process_http_source(source)
        elif method == "local_files":
            chunks = process_local_source(source)
        else:
            print(f"[WARN] unknown method '{method}' for {fw}")
            continue

        all_new_chunks.extend(chunks)

    if not all_new_chunks and not target_fw:
        print("[WARN] no chunks produced. Check raw_docs/ directories.")
        return

    # Incremental: preserve other frameworks already in corpus
    existing = CORPUS_FILE if target_fw else None
    if target_fw and existing and existing.exists():
        # Remove old chunks for this framework before merging
        kept = []
        with open(existing, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    c = json.loads(line)
                    if c.get("framework") != target_fw:
                        kept.append(c)
        # Write temp file without target framework
        tmp = CORPUS_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            for c in kept:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        existing = tmp

    total = save_corpus(all_new_chunks, existing_path=existing)

    # Clean up tmp file
    tmp = CORPUS_FILE.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()

    print(f"\nDone. {total} total chunks in corpus.")


if __name__ == "__main__":
    main()