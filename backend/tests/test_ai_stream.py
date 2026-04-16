import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.ollama import OllamaError, generate_stream


def _make_lines(*tokens: str) -> list[str]:
    """Simulate Ollama streaming: each token chunk has done=False, followed by a
    final empty-response chunk with done=True (matching actual Ollama wire format)."""
    lines = [json.dumps({"response": token, "done": False}) for token in tokens]
    lines.append(json.dumps({"response": "", "done": True}))
    return lines


def test_generate_stream_yields_tokens():
    mock_response = MagicMock()
    mock_response.iter_lines.return_value = _make_lines("Hello", " world", "!")
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("app.services.ollama.httpx.stream", return_value=mock_response):
        tokens = list(generate_stream("test prompt"))

    assert tokens == ["Hello", " world", "!"]


def test_generate_stream_raises_on_http_error():
    import httpx

    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad", request=MagicMock(), response=MagicMock()
    )

    with patch("app.services.ollama.httpx.stream", return_value=mock_response):
        with pytest.raises(OllamaError):
            list(generate_stream("test prompt"))


def test_generate_stream_error_raised_on_iteration_not_construction():
    """OllamaError surfaces when the generator is iterated, not when created."""
    import httpx

    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad", request=MagicMock(), response=MagicMock()
    )

    with patch("app.services.ollama.httpx.stream", return_value=mock_response):
        gen = generate_stream("test prompt")
        # Generator object created — no error yet
        with pytest.raises(OllamaError):
            next(gen)  # Error surfaces on first iteration
