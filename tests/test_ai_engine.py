import os
import pytest
from unittest.mock import patch, MagicMock
from ai_engine import get_ai_client, tailor_resume_for_job, generate_cover_letter

def test_get_ai_client_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fakekey")
    client = get_ai_client()
    assert hasattr(client, "chat")

def test_get_ai_client_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        get_ai_client()

@patch("ai_engine.openai.OpenAI")
def test_tailor_resume_for_job_success(mock_openai):
    # Mock OpenAI client and response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.arguments = '{"tailored_summary": "summary", "tailored_work_experience": []}'
    mock_response.choices = [MagicMock(message=MagicMock(tool_calls=[mock_tool_call]))]
    mock_client.chat.completions.create.return_value = mock_response

    resume_data = {"summary": "old", "work_experience": []}
    job_description = "Python developer"
    result = tailor_resume_for_job(mock_client, resume_data, job_description)
    assert isinstance(result, dict)
    assert "tailored_summary" in result

@patch("ai_engine.openai.OpenAI")
def test_tailor_resume_for_job_failure(mock_openai):
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")
    resume_data = {"summary": "old", "work_experience": []}
    job_description = "Python developer"
    result = tailor_resume_for_job(mock_client, resume_data, job_description)
    assert result is None

@patch("ai_engine.openai.OpenAI")
def test_generate_cover_letter_success(mock_openai):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Cover letter text"))]
    mock_client.chat.completions.create.return_value = mock_response

    tailored_resume = {"tailored_summary": "summary", "tailored_work_experience": []}
    result = generate_cover_letter(mock_client, tailored_resume, "Python Developer", "Acme Corp", "Jane Doe")
    assert isinstance(result, str)
    assert "Cover letter" in result or len(result) > 0

@patch("ai_engine.openai.OpenAI")
def test_generate_cover_letter_failure(mock_openai):
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")
    tailored_resume = {"tailored_summary": "summary", "tailored_work_experience": []}
    result = generate_cover_letter(mock_client, tailored_resume, "Python Developer", "Acme Corp", "Jane Doe")
    assert result is None