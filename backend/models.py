"""API request/response contracts (Pydantic v2).

Field names and types here are mirrored by the frontend
(frontend/src/types/api.ts) — do NOT rename or reshape them. Descriptions and
examples are documentation-only and safe to extend.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "tomato_leaf.jpg",
                "diagnosis": "Early Blight",
                "confidence": 0.70,
                "advice": "Remove affected leaves and improve airflow around the plant.",
                "needs_expert": False,
            }
        }
    )

    filename: str = Field(..., description="Name of the uploaded image file.")
    diagnosis: str = Field(
        ...,
        description=(
            "Predicted disease or condition — canonical English label used for "
            "knowledge-base matching (see diagnosis_localized for display)."
        ),
    )
    # Localized DISPLAY label for the diagnosis in the selected UI language
    # (Urdu script / Roman Urdu). Optional: absent for English answers and for
    # providers that do not produce one — the frontend then localizes itself.
    diagnosis_localized: Optional[str] = Field(
        None,
        description="Diagnosis label in the selected UI language, when localized.",
    )
    confidence: float = Field(
        ..., ge=0, le=1, description="Model confidence in the 0..1 range."
    )
    advice: str = Field(..., description="Recommended next action for the farmer.")
    needs_expert: bool = Field(
        ..., description="Whether the case should be escalated to a human expert."
    )
    # Present only when the AI provider failed or its response could not be
    # parsed — lets callers distinguish a real diagnosis from a fallback text.
    error: Optional[str] = Field(
        None, description="Provider error detail; None means the AI answered normally."
    )


class FollowupRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"question": "How often should I water after treatment?"}
        }
    )

    question: str = Field(
        ..., min_length=1, description="Farmer's follow-up question (non-empty)."
    )
    # Optional UI language selection ('en' | 'ur' | 'rom'); when omitted the
    # language stored with the latest diagnosis (if any) is reused.
    language: Optional[str] = Field(
        None, description="Language for the answer: 'en', 'ur' or 'rom'."
    )


class FollowupResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "How often should I water after treatment?",
                "answer": "Keep the soil moist but not waterlogged, roughly every 2 days.",
            }
        }
    )

    question: str = Field(..., description="Echo of the submitted question.")
    answer: str = Field(..., description="Assistant answer to the question.")
