# generation/ - Answer Generation
Owner: Mariem | Branch: feat/generation
Other file here: reranker.py (Ghassen)
Mariem also owns: agents/responder.py, agents/architecture_advisor.py, agents/code_assistant.py

## Pipeline
1. reranker.py (Ghassen) - re-score chunks
2. prompt_builder.py - format context + agent instructions + question
3. llm_client.py - Groq / Ollama
4. answer_generator.py - orchestrates all three

`build_prompt` and `call_llm` are also used by the agents in `agents/`
(architecture_advisor, code_assistant, evaluation_assistant).

## Output
`{answer: str, sources: [{chunk_id, url, framework, text}], query: str}`
