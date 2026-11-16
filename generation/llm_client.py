# generation/llm_client.py
# Owner: Ghassen

import httpx

from config.settings import GROQ_API_KEY, LLM_MODEL, LLM_PROVIDER, OLLAMA_URL

TEMPERATURE = 0.2      # low value: factual, grounded answers
MAX_TOKENS = 1500      # upper bound on the answer length
TIMEOUT = 120          # seconds (local models can be slow)


def _build_messages(prompt: str, system: str | None) -> list[dict]:
    """Chat format shared by Groq and Ollama."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _call_groq(prompt: str, system: str | None) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing: set it in config/.env or use LLM_PROVIDER=ollama")

    from groq import Groq  # imported here so Ollama users do not need the groq package

    client = Groq(api_key=GROQ_API_KEY, timeout=TIMEOUT)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=_build_messages(prompt, system),
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content or ""


def _call_ollama(prompt: str, system: str | None) -> str:
    payload = {
        "model": LLM_MODEL,
        "messages": _build_messages(prompt, system),
        "stream": False,
        "options": {"temperature": TEMPERATURE, "num_predict": MAX_TOKENS},
    }
    try:
        response = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=TIMEOUT)
        response.raise_for_status()
    except httpx.ConnectError as e:
        raise RuntimeError(f"Cannot reach Ollama at {OLLAMA_URL}: is it running?") from e
    return response.json()["message"]["content"]


def call_llm(prompt: str, system: str | None = None) -> str:
    """Send the prompt to the configured LLM provider and return the answer text."""
    if LLM_PROVIDER == "groq":
        return _call_groq(prompt, system)
    elif LLM_PROVIDER == "ollama":
        return _call_ollama(prompt, system)
    raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")