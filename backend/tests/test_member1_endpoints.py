import wave
from io import BytesIO
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import ai_pipeline, diagnosis_service


client = TestClient(app)
WAV_HEADER = b"RIFF\x24\x00\x00\x00WAVEfmt "


def test_health_reports_mock_mode_without_secret():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["configured"] is False
    assert body["mode"] == "mock"
    assert "DASHSCOPE_API_KEY" not in response.text


def test_health_never_returns_configured_secret(monkeypatch):
    secret = "credential-that-must-not-appear"
    monkeypatch.setenv("DASHSCOPE_API_KEY", secret)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["mode"] == "real"
    assert secret not in response.text


def test_image_only_diagnosis_uses_mock_mode():
    response = client.post("/diagnose", files={"image": ("plant.png", b"image", "image/png")})

    assert response.status_code == 200
    assert response.json()["filename"] == "plant.png"
    assert response.json()["needs_expert"] is True


def test_image_question_diagnosis_remains_compatible():
    response = client.post(
        "/diagnose",
        files={"image": ("plant.jpg", b"image", "image/jpeg")},
        data={"question": "Why are the leaves turning yellow?"},
    )

    assert response.status_code == 200
    assert "advice" in response.json()


def test_invalid_audio_is_rejected():
    response = client.post("/transcribe", files={"audio": ("voice.wav", b"not-audio", "audio/wav")})

    assert response.status_code == 400


def test_oversized_audio_is_rejected():
    oversized_audio = WAV_HEADER + b"0" * (10 * 1024 * 1024)
    response = client.post("/transcribe", files={"audio": ("voice.wav", oversized_audio, "audio/wav")})

    assert response.status_code == 400


def test_transcribe_uses_mock_provider():
    response = client.post("/transcribe", files={"audio": ("voice.wav", WAV_HEADER, "audio/wav")})

    assert response.status_code == 200
    assert response.json()["transcript_urdu"]


def test_speak_returns_valid_mock_wav():
    response = client.post("/speak", json={"text": "فصل کے لیے مشورہ"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert response.content.startswith(b"RIFF")
    with wave.open(BytesIO(response.content), "rb") as audio:
        assert audio.getnframes() > 0


def test_configured_provider_failure_does_not_become_mock_success(monkeypatch):
    class UpstreamFailure(Exception):
        status_code = 500

    class FailingOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, **kwargs):
            raise UpstreamFailure()

    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(ai_pipeline, "OpenAI", FailingOpenAI)
    diagnosis_service.reset_provider()

    response = client.post("/diagnose", files={"image": ("plant.jpg", b"image", "image/jpeg")})

    assert response.status_code == 502
    assert response.json()["code"] == "ai_upstream_failure"
    assert "diagnosis" not in response.json()
