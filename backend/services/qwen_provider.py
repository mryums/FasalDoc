"""
qwen_provider.py
================
Adapter that plugs Member 1's ai_pipeline.py functions into the
DiagnosisProvider interface that diagnosis_service.py expects.

This lets get_provider() swap MockDiagnosisProvider for the real thing
without changing anything else in the backend.
"""

import os

from services.ai_pipeline import (
    analyze_photo,
    generate_advice,
    load_knowledge_base,
)
from services.diagnosis_service import DiagnosisProvider

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

    def diagnose(self, filename, data=None, content_type=None):
        """
        Required by DiagnosisProvider. `data` is the raw photo bytes,
        `content_type` is the image mime type (e.g. "image/jpeg").
        Returns a dict shaped the same way MockDiagnosisProvider does,
        so routes.py doesn't need to change at all.
        """
        visual_findings = analyze_photo(data or b"")

        advice = generate_advice(
            visual_findings=visual_findings,
            user_urdu_query="",  # no spoken question yet at upload time
            knowledge_base_data=self.knowledge_base,
        )

        return {
            "filename": filename,
            "diagnosis": advice.get("diagnosis_english") or "Unknown",
            "confidence": (advice.get("confidence_score") or 0) / 100.0,
            "advice": advice.get("advice_urdu"),
            "needs_expert": advice.get("is_fallback", True),
        }

    def answer(self, question):
        """
        Required by DiagnosisProvider. Answers a farmer's follow-up
        question using the same knowledge base, without a fresh photo.
        """
        # No new photo for a follow-up question, so we tell generate_advice
        # to treat it as a general plant question rather than "not a plant".
        placeholder_findings = {
            "is_plant_photo": True,
            "crop_type_guess": "unknown",
            "visible_symptoms": [],
        }

        advice = generate_advice(
            visual_findings=placeholder_findings,
            user_urdu_query=question,
            knowledge_base_data=self.knowledge_base,
        )

        return advice.get("advice_urdu")
