"""qwen_provider.py
================
Adapter that plugs Member 1's ai_pipeline.py functions into the
DiagnosisProvider interface that diagnosis_service.py expects.

This lets get_provider() swap MockDiagnosisProvider for the real thing
without changing anything else in the backend.
"""

import os
from typing import Optional, Union

from backend.services.ai_pipeline import (
    analyze_photo,
    generate_advice,
    load_knowledge_base,
)
from backend.services.diagnosis_service import DiagnosisProvider, ImageInput

# knowledge_base.json lives in the top-level /data folder, two levels up
# from this file (backend/services/qwen_provider.py -> project_root/data/).
_KB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "knowledge_base.json"
)


class QwenDiagnosisProvider(DiagnosisProvider):
    """Real AI-powered provider, backed by Alibaba Cloud Model Studio (Qwen)."""

    def __init__(self):
        # Load the knowledge base once when the provider is created,
        # not on every single request.
        self.knowledge_base = load_knowledge_base(_KB_PATH)

    def diagnose(
        self,
        image: Union[ImageInput, str],
        data: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> dict:
        """Required by DiagnosisProvider. Accepts ImageInput (or individual args).

        Returns a dict shaped the same way MockDiagnosisProvider does.
        """
        if isinstance(image, ImageInput):
            filename = image.filename
            raw_bytes = image.data
            question_text = image.question or ""
        else:
            filename = str(image)
            raw_bytes = data or b""
            question_text = ""

        visual_findings = analyze_photo(raw_bytes)

        advice = generate_advice(
            visual_findings=visual_findings,
            user_urdu_query=question_text,
            knowledge_base_data=self.knowledge_base,
        )

        return {
            "filename": filename,
            "diagnosis": advice.get("diagnosis_english") or "Unknown",
            "confidence": (advice.get("confidence_score") or 0) / 100.0,
            "advice": advice.get("advice_urdu") or "",
            "needs_expert": advice.get("is_fallback", True),
        }

    def answer_followup(self, question: str, context: Optional[dict] = None) -> str:
        """Required by DiagnosisProvider.

        Answers a farmer's follow-up question using context if available.
        """
        placeholder_findings = {
            "is_plant_photo": True,
            "crop_type_guess": context.get("diagnosis", "unknown") if context else "unknown",
            "visible_symptoms": [],
        }

        user_query = question
        if context and context.get("original_question"):
            user_query = f"Original question: {context.get('original_question')}\nFollow-up: {question}"

        advice = generate_advice(
            visual_findings=placeholder_findings,
            user_urdu_query=user_query,
            knowledge_base_data=self.knowledge_base,
        )

        return advice.get("advice_urdu") or ""

    def answer(self, question: str) -> str:
        """Backwards compatibility alias for answer_followup."""
        return self.answer_followup(question)


def create_provider() -> DiagnosisProvider:
    """Factory function expected by diagnosis_service._build_provider()."""
    return QwenDiagnosisProvider()
