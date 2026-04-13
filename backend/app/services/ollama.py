import httpx

from app.config import settings


class OllamaError(RuntimeError):
    pass


def generate_text(prompt: str) -> str:
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": settings.ollama_temperature,
        },
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

    body = response.json()
    return body["response"]
