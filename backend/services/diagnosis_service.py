from io import BytesIO
import os
import wave
from typing import Any

from backend.services.ai_config import get_settings


_PLACEHOLDER_GEMINI_KEYS = {
    "",
    "your_key_here",
    "your-api-key",
    "your_api_key",
    "placeholder",
    "changeme",
    "replace_me",
    "replace-with-your-key",
    "none",
    "null",
}


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
_latest_context: dict[str, Any] | None = None


def _gemini_configured() -> bool:
    value = (os.getenv("GEMINI_API_KEY") or "").strip().strip("\"'")
    return bool(value) and value.lower() not in _PLACEHOLDER_GEMINI_KEYS


def get_provider() -> DiagnosisProvider:
    global _provider
    if _provider is None:
        # Preserve Member 1's Qwen priority when DashScope is configured.
        if get_settings().configured:
            from backend.services.qwen_provider import QwenDiagnosisProvider

            _provider = QwenDiagnosisProvider()
        elif _gemini_configured():
            try:
                from backend.services.gemini_provider import GeminiDiagnosisProvider

                _provider = GeminiDiagnosisProvider()
            except Exception:
                _provider = MockDiagnosisProvider()
        else:
            _provider = MockDiagnosisProvider()
    return _provider


def reset_provider() -> None:
    global _provider, _latest_context
    _provider = None
    _latest_context = None


def run_diagnosis(
    filename: str,
    data: bytes | None = None,
    content_type: str | None = None,
    question: str | None = None,
) -> dict[str, Any]:
    global _latest_context
    result = get_provider().diagnose(
        filename,
        data=data,
        content_type=content_type,
        question=question,
    )
    _latest_context = {
        "diagnosis": result.get("diagnosis"),
        "confidence": result.get("confidence"),
        "advice": result.get("advice"),
        "needs_expert": result.get("needs_expert"),
        "original_question": question,
    }
    return result


def get_latest_context() -> dict[str, Any] | None:
    return _latest_context.copy() if _latest_context is not None else None


def answer_followup(question: str) -> str:
    provider = get_provider()
    context = get_latest_context()
    answer_followup_method = getattr(provider, "answer_followup", None)
    if callable(answer_followup_method):
        return answer_followup_method(question, context=context)
    return provider.answer(question)


def transcribe_audio(audio_data: bytes, audio_format: str) -> dict[str, str]:
    return get_provider().transcribe(audio_data, audio_format)


def synthesize_speech(text: str) -> dict[str, Any]:
    return get_provider().synthesize(text)
