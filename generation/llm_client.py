# generation/llm_client.py
# Owner: Ghassen

from config.settings import GROQ_API_KEY, LLM_MODEL, LLM_PROVIDER, OLLAMA_URL


def call_llm(prompt: str, system: str | None = None) -> str:
    if LLM_PROVIDER == "groq":
        # TODO: groq.Groq(api_key=GROQ_API_KEY).chat.completions.create(model=LLM_MODEL, ...)
        raise NotImplementedError
    elif LLM_PROVIDER == "ollama":
        # TODO: POST f"{OLLAMA_URL}/api/chat" with model=LLM_MODEL (httpx)
        raise NotImplementedError
    raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")
