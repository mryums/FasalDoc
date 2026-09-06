"""Offline tests for backend/services/gemini_provider.py.

Every test injects a fake ``google.genai``-shaped client into
GeminiDiagnosisProvider, so NOTHING here ever makes a live network/API call.
"""
import json

import pytest

from backend.services.diagnosis_service import ImageInput
from backend.services.gemini_provider import GeminiDiagnosisProvider


class _FakeResponse:
    """Mimics the small slice of google.genai's response object we use."""

    def __init__(self, text):
        self.text = text


class _FakeModels:
    """Mimics client.models.generate_content(...)."""

    def __init__(self, response=None, exc=None):
        self._response = response
        self._exc = exc
        self.last_call = None

    def generate_content(self, **kwargs):
        self.last_call = kwargs
        if self._exc is not None:
            raise self._exc
        return self._response


class _FakeClient:
    def __init__(self, response=None, exc=None):
        self.models = _FakeModels(response=response, exc=exc)


def _make_provider(response_text=None, exc=None):
    fake_client = _FakeClient(
        response=_FakeResponse(response_text) if response_text is not None else None,
        exc=exc,
    )
    return GeminiDiagnosisProvider(client=fake_client), fake_client


VALID_IMAGE = ImageInput(
    filename="leaf.jpg",
    content_type="image/jpeg",
    data=b"fake-jpeg-bytes",
    question="Why are the leaves turning yellow?",
)


# --- Happy path --------------------------------------------------------------

def test_diagnose_returns_expected_contract_fields():
    payload = {
        "is_plant_photo": True,
        "diagnosis": "Early Blight",
        "confidence": 0.82,
        "advice": "Remove affected leaves and improve airflow.",
        "needs_expert": False,
    }
    provider, _ = _make_provider(response_text=json.dumps(payload))

    result = provider.diagnose(VALID_IMAGE)

    assert set(result.keys()) >= {"filename", "diagnosis", "confidence", "advice", "needs_expert"}
    assert result["filename"] == "leaf.jpg"
    assert result["diagnosis"] == "Early Blight"
    assert result["confidence"] == pytest.approx(0.82)
    assert result["advice"]
    assert result["needs_expert"] is False


def test_diagnose_sends_image_and_question_together():
    payload = {
        "is_plant_photo": True,
        "diagnosis": "Powdery Mildew",
        "confidence": 0.9,
        "advice": "Apply fungicide.",
        "needs_expert": False,
    }
    provider, fake_client = _make_provider(response_text=json.dumps(payload))

    provider.diagnose(VALID_IMAGE)

    call = fake_client.models.last_call
    assert call is not None
    contents = call["contents"]
    # First content item is the image part, second is the question-derived prompt.
    assert len(contents) == 2
    assert VALID_IMAGE.question in contents[1]


def test_diagnose_handles_markdown_fenced_json():
    payload = {
        "is_plant_photo": True,
        "diagnosis": "Leaf Rust",
        "confidence": 0.75,
        "advice": "Use a rust-resistant variety next season.",
        "needs_expert": False,
    }
    fenced = "```json\n" + json.dumps(payload) + "\n```"
    provider, _ = _make_provider(response_text=fenced)

    result = provider.diagnose(VALID_IMAGE)
    assert result["diagnosis"] == "Leaf Rust"


# --- Non-plant image ----------------------------------------------------------

def test_diagnose_handles_non_plant_image():
    payload = {
        "is_plant_photo": False,
        "diagnosis": "Unknown",
        "confidence": 0.0,
        "advice": "That doesn't look like a plant.",
        "needs_expert": True,
    }
    provider, _ = _make_provider(response_text=json.dumps(payload))

    result = provider.diagnose(VALID_IMAGE)

    assert result["needs_expert"] is True
    assert result["confidence"] == 0.0
    assert result["diagnosis"] == "Unknown"


# --- Low confidence enforcement ----------------------------------------------

def test_diagnose_enforces_confidence_threshold_in_python():
    # Model claims a diagnosis but with low confidence and needs_expert=False;
    # our code must override needs_expert/advice regardless of what the model said.
    payload = {
        "is_plant_photo": True,
        "diagnosis": "Possible fungal infection",
        "confidence": 0.25,
        "advice": "Definitely fungal, spray immediately.",
        "needs_expert": False,
    }
    provider, _ = _make_provider(response_text=json.dumps(payload))

    result = provider.diagnose(VALID_IMAGE)

    assert result["needs_expert"] is True
    assert "expert" in result["advice"].lower() or "extension" in result["advice"].lower()


# --- API errors ---------------------------------------------------------------

def test_diagnose_handles_api_error_gracefully():
    provider, _ = _make_provider(exc=RuntimeError("network is down"))

    result = provider.diagnose(VALID_IMAGE)

    assert result["diagnosis"] == "Unknown"
    assert result["confidence"] == 0.0
    assert result["needs_expert"] is True
    assert "error" in result


# --- Malformed responses -------------------------------------------------------

def test_diagnose_handles_malformed_json_response():
    provider, _ = _make_provider(response_text="not json at all, sorry!")

    result = provider.diagnose(VALID_IMAGE)

    assert result["diagnosis"] == "Unknown"
    assert result["needs_expert"] is True
    assert "error" in result


def test_diagnose_handles_empty_response_text():
    provider, _ = _make_provider(response_text="")

    result = provider.diagnose(VALID_IMAGE)

    assert result["diagnosis"] == "Unknown"
    assert result["needs_expert"] is True


def test_diagnose_handles_missing_fields_in_valid_json():
    # Valid JSON but missing several expected keys should not crash.
    provider, _ = _make_provider(response_text=json.dumps({"is_plant_photo": True}))

    result = provider.diagnose(VALID_IMAGE)

    assert result["filename"] == "leaf.jpg"
    assert 0 <= result["confidence"] <= 1
    assert isinstance(result["needs_expert"], bool)
    assert result["advice"]


# --- Missing API key -----------------------------------------------------------

def test_missing_api_key_raises_before_any_request(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        GeminiDiagnosisProvider()


def test_placeholder_api_key_raises(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "your_key_here")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        GeminiDiagnosisProvider()


# --- Follow-up -------------------------------------------------------------

def test_answer_followup_returns_text():
    provider, _ = _make_provider(response_text="Water every two days after treatment.")
    answer = provider.answer_followup("How often should I water?", context={"diagnosis": "Early Blight", "confidence": 0.8})
    assert isinstance(answer, str)
    assert answer.strip()


def test_answer_followup_handles_api_error():
    provider, _ = _make_provider(exc=RuntimeError("timeout"))
    answer = provider.answer_followup("How often should I water?")
    assert isinstance(answer, str)
    assert answer.strip()
