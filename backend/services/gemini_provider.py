"""Gemini-backed DiagnosisProvider for FasalDoc."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

from backend.services.diagnosis_service import DiagnosisProvider

logger = logging.getLogger("fasaldoc.gemini_provider")

DEFAULT_MODEL = "gemini-3.6-flash"
CONFIDENCE_THRESHOLD = 0.60

FALLBACK_ADVICE = (
    "We could not confidently diagnose this from the photo and question "
    "provided. To avoid giving potentially wrong advice, please consult a "
    "local agriculture expert or extension officer for an in-person assessment."
)

NOT_A_PLANT_ADVICE = (
    "This image does not appear to show a plant or crop. Please upload a "
    "clear photo of the affected leaf, stem, or plant so we can help diagnose the issue."
)

GEMINI_SYSTEM_PROMPT = """You are "FasalDoc", an agricultural vision-and-advisory assistant that helps farmers diagnose crop health issues from a photo and an optional question. You are NOT a certain diagnosis tool -- you combine what is visually observable in the image with the farmer's question to give honest, conservative guidance.

Respond with ONLY a JSON object (no extra text, no markdown code fences) with exactly this structure:
{
  "is_plant_photo": true or false,
  "diagnosis": "short diagnosis label, or 'Unknown' if unclear",
  "confidence": 0.0-1.0 number,
  "advice": "clear, farmer-friendly advice text, 2-5 sentences",
  "needs_expert": true or false
}

Rules:
- If the image does NOT show a plant/crop at all, set "is_plant_photo" to false, "diagnosis" to "Unknown", "confidence" to 0.0, "needs_expert" to true, and "advice" to a short note asking the farmer to upload a clear plant photo. Do NOT invent crop symptoms.
- Set confidence honestly: high (0.7-1.0) only when symptoms clearly match one specific diagnosis; medium (0.4-0.69) when partially clear; low (0.0-0.39) when blurry or ambiguous.
- Set needs_expert to true whenever confidence is below 0.6, the case looks severe, or you are not confident in a specific diagnosis.
- Be conservative -- it is much better to admit uncertainty than to confidently give wrong advice.
- Use the farmer's question to focus advice, but never let it override what is actually visible in the image.
"""


def _extract_json(raw_text: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw_text:
        return None
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = re.sub(r"^json\s*", "", text, count=1, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON from Gemini output: %s", text[:300])
    return None


def _guess_mime_type(content_type: Optional[str], filename: str) -> str:
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if content_type in allowed:
        return content_type
    lower_name = (filename or "").lower()
    if lower_name.endswith(".png"):
        return "image/png"
    if lower_name.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


class GeminiDiagnosisProvider(DiagnosisProvider):
    """DiagnosisProvider backed by Gemini vision + text."""

    def __init__(self, client: Optional[Any] = None, model: Optional[str] = None):
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
        self._client = client if client is not None else self._build_client()

    @staticmethod
    def _build_client() -> Any:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.strip().lower() in {"", "your_key_here"}:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set. Get a key "
                "from Google AI Studio and export it before running the app."
            )
        from google import genai  # type: ignore
        return genai.Client(api_key=api_key)

    def diagnose(
        self,
        filename: str,
        data: bytes | None = None,
        content_type: str | None = None,
        question: str | None = None,
    ) -> dict[str, Any]:
        question_text = (question or "").strip()
        try:
            from google.genai import types  # type: ignore

            mime_type = _guess_mime_type(content_type, filename)
            prompt_text = (
                f"Farmer's question: {question_text}"
                if question_text
                else "The farmer did not provide a written question. Diagnose the crop issue from the photo alone."
            )
            response = self._client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=data or b"", mime_type=mime_type),
                    prompt_text,
                ],
                config=types.GenerateContentConfig(
                    system_instruction=GEMINI_SYSTEM_PROMPT,
                    temperature=0.2,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Gemini diagnose() call failed")
            return {
                "filename": filename,
                "diagnosis": "Unknown",
                "confidence": 0.0,
                "advice": FALLBACK_ADVICE,
                "needs_expert": True,
                "error": f"Gemini request failed: {exc}",
            }

        raw_text = getattr(response, "text", None)
        parsed = _extract_json(raw_text)
        if parsed is None:
            return {
                "filename": filename,
                "diagnosis": "Unknown",
                "confidence": 0.0,
                "advice": FALLBACK_ADVICE,
                "needs_expert": True,
                "error": "Could not parse Gemini response.",
            }

        if parsed.get("is_plant_photo") is False:
            return {
                "filename": filename,
                "diagnosis": "Unknown",
                "confidence": 0.0,
                "advice": parsed.get("advice") or NOT_A_PLANT_ADVICE,
                "needs_expert": True,
            }

        try:
            confidence = float(parsed.get("confidence", 0) or 0)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        diagnosis = parsed.get("diagnosis") or "Unknown"
        advice = parsed.get("advice") or ""
        needs_expert = bool(parsed.get("needs_expert", False))
        if confidence < CONFIDENCE_THRESHOLD:
            needs_expert = True
            advice = FALLBACK_ADVICE

        return {
            "filename": filename,
            "diagnosis": diagnosis,
            "confidence": confidence,
            "advice": advice or FALLBACK_ADVICE,
            "needs_expert": needs_expert,
        }

    def answer(self, question: str) -> str:
        prompt = (
            "You are FasalDoc, an agricultural advisor answering a farmer's follow-up question. "
            "Reply in plain text (no JSON), 2-4 sentences, clear and actionable.\n\n"
            f"Follow-up question: {question}"
        )
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=[prompt],
            )
        except Exception:  # noqa: BLE001
            logger.exception("Gemini answer() call failed")
            return FALLBACK_ADVICE
        return (getattr(response, "text", None) or "").strip() or FALLBACK_ADVICE

    # Backward-compatible helper retained for existing Gemini tests/callers.
    def answer_followup(self, question: str, context: Optional[dict] = None) -> str:
        context_note = ""
        if context and context.get("diagnosis"):
            context_note = (
                f"Earlier diagnosis for this session: {context.get('diagnosis')} "
                f"(confidence {context.get('confidence')}). "
            )
        prompt = (
            "You are FasalDoc, an agricultural advisor answering a farmer's follow-up question. "
            "Reply in plain text (no JSON), 2-4 sentences, clear and actionable.\n\n"
            f"{context_note}Follow-up question: {question}"
        )
        try:
            response = self._client.models.generate_content(model=self.model, contents=[prompt])
        except Exception:  # noqa: BLE001
            logger.exception("Gemini answer_followup() call failed")
            return FALLBACK_ADVICE
        return (getattr(response, "text", None) or "").strip() or FALLBACK_ADVICE


def create_provider() -> DiagnosisProvider:
    return GeminiDiagnosisProvider()
