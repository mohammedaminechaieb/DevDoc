# generation/ - Answer Generation
Primary owner: Mariem | Branch: feat/generation
Cross-module contribution here: Amine (reranker.py)
Mariem contributes to: api/routes/query.py

## Pipeline
1. reranker.py (Amine) - re-score chunks
2. prompt_builder.py - format context + question
3. llm_client.py - Groq / Ollama
4. answer_generator.py - orchestrates all three

## Output
{answer: str, sources: [{url, framework, text}], query: str}
