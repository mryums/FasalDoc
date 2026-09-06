from types import SimpleNamespace

import pytest

from backend.services import ai_pipeline, diagnosis_service, qwen_provider
from backend.services.ai_config import configured_api_key, get_settings
from backend.services.ai_errors import AIInvalidCredentialError, AIInvalidModelOutputError
from backend.services.diagnosis_service import MockDiagnosisProvider
from backend.utils.validators import image_format_from_mime


def response_with_content(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class FakeOpenAI:
    response_content = "{}"
    error = None
    calls = []
    init_arguments = []

    def __init__(self, *args, **kwargs):
        type(self).init_arguments.append((args, kwargs))
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        type(self).calls.append(kwargs)
        if type(self).error:
            raise type(self).error
        return response_with_content(type(self).response_content)


def test_placeholder_keys_are_not_configured(monkeypatch):
    for value in ("", " your_key_here ", "placeholder", "'changeme'"):
        monkeypatch.setenv("DASHSCOPE_API_KEY", value)
        assert configured_api_key() is None


def test_missing_credential_uses_mock_provider():
    provider = diagnosis_service.get_provider()
    assert isinstance(provider, MockDiagnosisProvider)
    assert get_settings().diagnostics()["mode"] == "mock"


def test_configured_credential_uses_qwen_provider(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    provider = diagnosis_service.get_provider()
    assert isinstance(provider, qwen_provider.QwenDiagnosisProvider)
    assert get_settings().diagnostics()["mode"] == "real"


def test_openai_client_uses_configured_timeout_and_retries(monkeypatch):
    FakeOpenAI.init_arguments.clear()
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("DASHSCOPE_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("DASHSCOPE_MAX_RETRIES", "3")
    monkeypatch.setattr(ai_pipeline, "OpenAI", FakeOpenAI)

    ai_pipeline._get_client()

    _, kwargs = FakeOpenAI.init_arguments[-1]
    assert kwargs["timeout"] == 45
    assert kwargs["max_retries"] == 3
    assert kwargs["api_key"] == "test-key"


def test_invalid_credentials_become_typed_error(monkeypatch):
    class UnauthorizedError(Exception):
        status_code = 401

    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    FakeOpenAI.error = UnauthorizedError()
    monkeypatch.setattr(ai_pipeline, "OpenAI", FakeOpenAI)

    with pytest.raises(AIInvalidCredentialError):
        ai_pipeline.analyze_photo(b"photo", "png")
    FakeOpenAI.error = None


def test_vision_json_and_mime_format_are_used(monkeypatch):
    FakeOpenAI.calls.clear()
    FakeOpenAI.response_content = """```json
    {"is_plant_photo": true, "crop_type_guess": "tomato", "visible_symptoms": ["yellowing"]}
    ```"""
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(ai_pipeline, "OpenAI", FakeOpenAI)

    findings = ai_pipeline.analyze_photo(b"photo", image_format_from_mime("image/png"))

    assert findings["is_plant_photo"] is True
    assert findings["crop_type_guess"] == "tomato"
    image_url = FakeOpenAI.calls[-1]["messages"][1]["content"][0]["image_url"]["url"]
    assert image_url.startswith("data:image/png;base64,")
    assert image_format_from_mime("image/webp") == "webp"
    assert image_format_from_mime("image/gif") is None


def test_invalid_knowledge_base_is_rejected(tmp_path):
    invalid_path = tmp_path / "knowledge_base.json"
    invalid_path.write_text("{}", encoding="utf-8")

    with pytest.raises(AIInvalidModelOutputError):
        ai_pipeline.load_knowledge_base(invalid_path)


def test_non_plant_shortcut_never_calls_provider():
    result = ai_pipeline.generate_advice({"is_plant_photo": False}, "", [])

    assert result["confidence_score"] == 0
    assert result["is_fallback"] is True
    assert result["advice_urdu"] == ai_pipeline.NOT_A_PLANT_ADVICE_URDU


def test_confidence_threshold_is_enforced_in_python(monkeypatch):
    FakeOpenAI.response_content = '{"confidence_score": 59, "advice_urdu": "unsafe advice"}'
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(ai_pipeline, "OpenAI", FakeOpenAI)

    result = ai_pipeline.generate_advice(
        {"is_plant_photo": True, "visible_symptoms": [], "crop_type_guess": "tomato"},
        "میرے پتے پیلے ہیں",
        [],
    )

    assert result["confidence_score"] == 59
    assert result["is_fallback"] is True
    assert result["advice_urdu"] == ai_pipeline.FALLBACK_ADVICE_URDU


def test_question_is_forwarded_to_advice_generation(monkeypatch):
    captured = {}
    provider = qwen_provider.QwenDiagnosisProvider()

    monkeypatch.setattr(
        qwen_provider,
        "analyze_photo",
        lambda data, image_format: {"is_plant_photo": True, "visible_symptoms": [], "crop_type_guess": "tomato"},
    )

    def fake_generate_advice(visual_findings, user_urdu_query, knowledge_base_data):
        captured["question"] = user_urdu_query
        return {
            "diagnosis_english": "Tomato issue",
            "confidence_score": 80,
            "advice_urdu": "محفوظ مشورہ",
            "is_fallback": False,
        }

    monkeypatch.setattr(qwen_provider, "generate_advice", fake_generate_advice)
    result = provider.diagnose("plant.jpg", b"photo", "image/jpeg", "Why are the leaves turning yellow?")

    assert result["diagnosis"] == "Tomato issue"
    assert captured["question"] == "Why are the leaves turning yellow?"
