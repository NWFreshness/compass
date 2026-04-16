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


import uuid
from app.services.ai_analysis import analyze_student_stream, analyze_class_stream


def _make_db_with_student():
    student = MagicMock()
    student.id = uuid.uuid4()
    student.name = "Test Student"
    student.grade_level = 5

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = student
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []

    rec = MagicMock()
    rec.id = uuid.uuid4()
    db.refresh = lambda r: setattr(r, "id", rec.id)
    return db, student


def test_analyze_student_stream_yields_tokens_then_done():
    db, student = _make_db_with_student()
    tokens = ["Hello", " world"]

    with patch("app.services.ai_analysis.ollama_client.generate_stream", return_value=iter(tokens)):
        results = list(analyze_student_stream(db, student_id=student.id, created_by=uuid.uuid4()))

    assert results[:-1] == tokens
    assert results[-1].startswith("\n__DONE__:")
    db.add.assert_called_once()
    db.commit.assert_called_once()


def _make_db_with_class():
    cls = MagicMock()
    cls.id = uuid.uuid4()
    cls.name = "Test Class"
    cls.grade_level = 5

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = cls
    db.query.return_value.filter.return_value.all.return_value = []

    rec = MagicMock()
    rec.id = uuid.uuid4()
    db.refresh = lambda r: setattr(r, "id", rec.id)
    return db, cls


def test_analyze_class_stream_yields_tokens_then_done():
    db, cls = _make_db_with_class()
    tokens = ["Class", " analysis"]

    with patch("app.services.ai_analysis.ollama_client.generate_stream", return_value=iter(tokens)):
        results = list(analyze_class_stream(db, class_id=cls.id, created_by=uuid.uuid4()))

    assert results[:-1] == tokens
    assert results[-1].startswith("\n__DONE__:")
    db.add.assert_called_once()
    db.commit.assert_called_once()
