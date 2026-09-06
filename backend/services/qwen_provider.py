from typing import Any

from backend.services.ai_errors import AIInvalidModelOutputError
from backend.services.ai_pipeline import (
    analyze_photo,
    generate_advice,
    load_knowledge_base,
    speech_to_text,
    text_to_speech,
)
from backend.services.diagnosis_service import DiagnosisProvider
from backend.utils.validators import image_format_from_mime


class QwenDiagnosisProvider(DiagnosisProvider):
    def __init__(self) -> None:
        self.knowledge_base = load_knowledge_base()

    def diagnose(
        self,
        filename: str,
        data: bytes | None = None,
        content_type: str | None = None,
        question: str | None = None,
    ) -> dict[str, Any]:
        image_format = image_format_from_mime(content_type)
        if not image_format:
            raise AIInvalidModelOutputError()

        visual_findings = analyze_photo(data or b"", image_format=image_format)
        advice = generate_advice(
            visual_findings=visual_findings,
            user_urdu_query=(question or "").strip(),
            knowledge_base_data=self.knowledge_base,
        )
        advice_text = advice.get("advice_urdu")
        if not isinstance(advice_text, str) or not advice_text.strip():
            raise AIInvalidModelOutputError()

        return {
            "filename": filename,
            "diagnosis": str(advice.get("diagnosis_english") or "Unknown"),
            "confidence": max(0.0, min(1.0, float(advice.get("confidence_score", 0)) / 100.0)),
            "advice": advice_text,
            "needs_expert": bool(advice.get("is_fallback", True)),
        }

    def answer(self, question: str) -> str:
        advice = generate_advice(
            visual_findings={"is_plant_photo": True, "crop_type_guess": "unknown", "visible_symptoms": []},
            user_urdu_query=question,
            knowledge_base_data=self.knowledge_base,
        )
        answer = advice.get("advice_urdu")
        if not isinstance(answer, str) or not answer.strip():
            raise AIInvalidModelOutputError()
        return answer

    def transcribe(self, audio_data: bytes, audio_format: str) -> dict[str, str]:
        return speech_to_text(audio_data, audio_format)

    def synthesize(self, text: str) -> dict[str, Any]:
        return text_to_speech(text)
