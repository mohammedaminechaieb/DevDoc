# generation/llm_client.py
# Owner: Ghassen
#
# One function for the whole project. Provider is chosen in config/.env (LLM_PROVIDER):
#   gemini -> Google Gemini (GEMINI_API_KEY) | groq -> Groq (GROQ_API_KEY) | ollama -> local (OLLAMA_URL)

import httpx

from config.settings import GEMINI_API_KEY, GROQ_API_KEY, LLM_MODEL, LLM_PROVIDER, OLLAMA_URL

TEMPERATURE = 0.2      # low value: factual, grounded answers
MAX_TOKENS = 1500      # upper bound on the answer length
TIMEOUT = 120          # seconds (local models can be slow)

_gemini_client = None


def _build_messages(prompt: str, system: str | None) -> list[dict]:
    """Chat format shared by Groq and Ollama."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _call_gemini(prompt: str, system: str | None) -> str:
    global _gemini_client
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing: set it in config/.env or use LLM_PROVIDER=groq|ollama")

    from google import genai            # imported here so other providers do not need the package
    from google.genai import types

    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    response = _gemini_client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_TOKENS,
        ),
    )
    return response.text or ""


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


PROVIDERS = {"gemini": _call_gemini, "groq": _call_groq, "ollama": _call_ollama}


def call_llm(prompt: str, system: str | None = None) -> str:
    """Send the prompt to the configured LLM provider and return the answer text."""
    try:
        return PROVIDERS[LLM_PROVIDER](prompt, system)
    except KeyError:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER} (expected gemini | groq | ollama)")
