"""
LLM integration via Ollama — Phase 2.

Supports:
- Full conversation history context
- System prompt injection
- Streaming (token by token) via ask_llm_stream()
- Non-streaming via ask_llm()
- Health check to detect if Ollama is running
- Graceful error messages instead of 500 crashes
"""
import json
import logging
from collections.abc import Generator

import requests

from app.config import settings

logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────
# Edit this to give Mistral its persona and constraints.
SYSTEM_PROMPT = """You are a helpful, concise, and friendly AI assistant.
Answer the user's questions clearly. If you are unsure about something, say so.
Do not make up facts. Keep responses focused and well-structured."""


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(messages: list[dict]) -> str:
    """
    Convert a conversation history list into a Mistral-compatible prompt string.

    Mistral (via Ollama /api/generate) expects a plain text prompt.
    We format it as a clear role-labelled dialogue so the model tracks context.

    messages: [{"role": "user"|"assistant", "content": "..."}]
    """
    lines = [f"System: {SYSTEM_PROMPT}\n"]
    for m in messages:
        role_label = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{role_label}: {m['content']}")
    lines.append("Assistant:")          # cue the model to reply
    return "\n".join(lines)


# ── Health check ──────────────────────────────────────────────────────────────

def check_ollama_health() -> tuple[bool, str]:
    """
    Returns (is_healthy: bool, message: str).
    Call this on startup or before the first request to give a clear error.
    """
    try:
        r = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        if not any(settings.OLLAMA_MODEL in m for m in models):
            return False, (
                f"Model '{settings.OLLAMA_MODEL}' not found in Ollama. "
                f"Run: ollama pull {settings.OLLAMA_MODEL}"
            )
        return True, f"Ollama healthy. Model '{settings.OLLAMA_MODEL}' ready."
    except requests.ConnectionError:
        return False, (
            f"Cannot reach Ollama at {settings.OLLAMA_BASE_URL}. "
            "Is it running? Run: ollama serve"
        )
    except Exception as e:
        return False, f"Ollama health check failed: {e}"


# ── Non-streaming ─────────────────────────────────────────────────────────────

def ask_llm(messages: list[dict]) -> str:
    """
    Send the full conversation history to Ollama and return the complete reply.

    Raises:
        LLMUnavailableError  — Ollama is not running
        LLMResponseError     — Ollama returned an unexpected response
    """
    prompt = _build_prompt(messages)

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 1024,    # max tokens in reply
                },
            },
            timeout=120,
        )
        response.raise_for_status()

    except requests.ConnectionError:
        logger.error("Ollama connection refused at %s", settings.OLLAMA_BASE_URL)
        raise LLMUnavailableError(
            f"Cannot reach Ollama at {settings.OLLAMA_BASE_URL}. "
            "Make sure Ollama is running: ollama serve"
        )
    except requests.Timeout:
        raise LLMUnavailableError("Ollama timed out. The model may still be loading.")
    except requests.HTTPError as e:
        raise LLMResponseError(f"Ollama returned HTTP {e.response.status_code}: {e.response.text}")

    data = response.json()
    text = data.get("response", "").strip()
    if not text:
        raise LLMResponseError("Ollama returned an empty response.")

    logger.info(
        "LLM replied | tokens_in=%s tokens_out=%s duration_ms=%s",
        data.get("prompt_eval_count"),
        data.get("eval_count"),
        round(data.get("total_duration", 0) / 1_000_000),   # ns → ms
    )
    return text


# ── Streaming ─────────────────────────────────────────────────────────────────

def ask_llm_stream(messages: list[dict]) -> Generator[str, None, None]:
    """
    Yields response tokens one by one as they arrive from Ollama.
    Use this with FastAPI's StreamingResponse for a typewriter effect.

    Usage in a route:
        from fastapi.responses import StreamingResponse
        return StreamingResponse(ask_llm_stream(history), media_type="text/plain")
    """
    prompt = _build_prompt(messages)

    try:
        with requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": True,
                "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 1024},
            },
            stream=True,
            timeout=120,
        ) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                chunk = json.loads(raw_line)
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break

    except requests.ConnectionError:
        yield "\n[Error: Ollama is not running. Start it with: ollama serve]"
    except Exception as e:
        yield f"\n[Error: {e}]"


# ── Custom exceptions ─────────────────────────────────────────────────────────

class LLMUnavailableError(Exception):
    """Raised when Ollama cannot be reached."""


class LLMResponseError(Exception):
    """Raised when Ollama returns an unexpected or empty response."""
