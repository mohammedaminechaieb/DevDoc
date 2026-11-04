# generation/llm_client.py
# Primary owner: Mariem

from config.settings import LLM_PROVIDER, LLM_MODEL

def call_llm(prompt: str) -> str:
    if LLM_PROVIDER == "groq":
        # TODO: call Groq API, return response text
        raise NotImplementedError
    elif LLM_PROVIDER == "ollama":
        # TODO: call local Ollama endpoint
        raise NotImplementedError
    raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")
