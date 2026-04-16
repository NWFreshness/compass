import json
from collections.abc import Iterator

import httpx

from app.config import settings


class OllamaError(RuntimeError):
    pass


def generate_text(prompt: str) -> str:
    """Call local Ollama and return the generated text."""
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": settings.ollama_temperature},
    }
    try:
        response = httpx.post(
            f"{settings.ollama_url}/api/generate",
            json=payload,
            timeout=settings.ollama_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError("Ollama request failed") from exc

    return response.json()["response"]


def generate_stream(prompt: str) -> Iterator[str]:
    """Call local Ollama with streaming and yield each token."""
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": settings.ollama_temperature},
    }
    try:
        with httpx.stream(
            "POST",
            f"{settings.ollama_url}/api/generate",
            json=payload,
            timeout=settings.ollama_timeout_seconds,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                yield data["response"]
                if data.get("done"):
                    break
    except httpx.HTTPError as exc:
        raise OllamaError("Ollama request failed") from exc
