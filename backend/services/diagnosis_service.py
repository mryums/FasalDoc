from io import BytesIO
import wave
from typing import Any

from backend.services.ai_config import get_settings


class DiagnosisProvider:
    def diagnose(
        self,
        filename: str,
        data: bytes | None = None,
        content_type: str | None = None,
        question: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def answer(self, question: str) -> str:
        raise NotImplementedError

    def transcribe(self, audio_data: bytes, audio_format: str) -> dict[str, str]:
        raise NotImplementedError

    def synthesize(self, text: str) -> dict[str, Any]:
        raise NotImplementedError


class MockDiagnosisProvider(DiagnosisProvider):
    def diagnose(
        self,
        filename: str,
        data: bytes | None = None,
        content_type: str | None = None,
        question: str | None = None,
    ) -> dict[str, Any]:
        return {
            "filename": filename,
            "diagnosis": "Unknown plant disease",
            "confidence": 0.50,
            "advice": "Please consult an agricultural expert for confirmation.",
            "needs_expert": True,
        }

    def answer(self, question: str) -> str:
        return "This is a preliminary response. For accurate agricultural advice, please consult an expert."

    def transcribe(self, audio_data: bytes, audio_format: str) -> dict[str, str]:
        return {"transcript_urdu": "یہ ایک نمونہ اردو نقل ہے۔"}

    def synthesize(self, text: str) -> dict[str, Any]:
        buffer = BytesIO()
        with wave.open(buffer, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(8000)
            output.writeframes(b"\x00\x00" * 1600)
        return {"audio_bytes": buffer.getvalue(), "audio_format": "wav"}


_provider: DiagnosisProvider | None = None


def get_provider() -> DiagnosisProvider:
    global _provider
    if _provider is None:
        if get_settings().configured:
            from backend.services.qwen_provider import QwenDiagnosisProvider

            _provider = QwenDiagnosisProvider()
        else:
            _provider = MockDiagnosisProvider()
    return _provider


def reset_provider() -> None:
    global _provider
    _provider = None


def run_diagnosis(
    filename: str,
    data: bytes | None = None,
    content_type: str | None = None,
    question: str | None = None,
) -> dict[str, Any]:
    return get_provider().diagnose(filename, data=data, content_type=content_type, question=question)


def answer_followup(question: str) -> str:
    return get_provider().answer(question)


def transcribe_audio(audio_data: bytes, audio_format: str) -> dict[str, str]:
    return get_provider().transcribe(audio_data, audio_format)


def synthesize_speech(text: str) -> dict[str, Any]:
    return get_provider().synthesize(text)
