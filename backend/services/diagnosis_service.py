"""Diagnosis service layer (M2 backend).

This module defines the contract between the FastAPI routes and the AI
backend. Routes call the module-level helpers (:func:`run_diagnosis` and
:func:`answer_followup`); they never hardcode AI logic.

Plugging in the real AI (Member 1 — Qwen / Alibaba Cloud DashScope):
    1. Create ``backend/services/qwen_provider.py`` exposing a factory::

           def create_provider() -> "DiagnosisProvider":
               ...

       whose object implements the :class:`DiagnosisProvider` protocol below.
    2. Set ``DASHSCOPE_API_KEY`` (and any other config) in the environment.

Nothing in the routes needs to change. If the credentials are missing or the
real provider cannot be built, the service transparently falls back to the
offline :class:`MockDiagnosisProvider`, so the app keeps working without
Alibaba Cloud access.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional, Protocol

logger = logging.getLogger("fasaldoc.diagnosis_service")


@dataclass(frozen=True)
class ImageInput:
    """Everything a diagnosis provider needs about an uploaded image."""

    filename: str
    content_type: str
    data: bytes


class DiagnosisProvider(Protocol):
    """Stable interface the routes depend on.

    Implement this in the real Qwen/Alibaba provider; the mock below already
    satisfies it. Keep these two method signatures unchanged so no route code
    has to be touched when the real AI layer lands.
    """

    def diagnose(self, image: ImageInput) -> dict:
        ...

    def answer_followup(self, question: str, context: Optional[dict] = None) -> str:
        ...


class MockDiagnosisProvider:
    """TEMPORARY MOCK — offline fallback used when no AI is configured.

    Returns deterministic, contract-valid responses so the whole app (and the
    test suite) runs without any network/Alibaba Cloud access.
    """

    def diagnose(self, image: ImageInput) -> dict:
        return {
            "filename": image.filename,
            "diagnosis": "Early Blight",
            "confidence": 0.70,
            "advice": "Remove affected leaves and improve airflow around the plant.",
            "needs_expert": False,
        }

    def answer_followup(self, question: str, context: Optional[dict] = None) -> str:
        return "This is a temporary response. AI integration will be added later."


def _looks_configured(key: str) -> bool:
    """True only when a real, non-placeholder API key is present."""
    return bool(key) and key.strip().lower() not in {"", "your_key_here"}


def _build_provider() -> DiagnosisProvider:
    """Select the active provider once, at first use.

    Prefers Member 1's real provider when credentials exist; otherwise (or on
    any construction error) safely falls back to the offline mock.
    """
    if _looks_configured(os.getenv("DASHSCOPE_API_KEY", "")):
        try:
            from backend.services.qwen_provider import create_provider  # type: ignore

            return create_provider()
        except Exception as exc:  # pragma: no cover - depends on Member 1's module
            logger.warning(
                "Qwen provider unavailable (%s); using offline mock fallback.", exc
            )
    return MockDiagnosisProvider()


_provider: Optional[DiagnosisProvider] = None


def get_provider() -> DiagnosisProvider:
    global _provider
    if _provider is None:
        _provider = _build_provider()
    return _provider


def reset_provider() -> None:
    """Clear the cached provider. Intended for tests / runtime reconfiguration."""
    global _provider
    _provider = None


# --- Helpers used by the routes -------------------------------------------

def run_diagnosis(
    filename: str,
    *,
    data: bytes = b"",
    content_type: str = "image/jpeg",
) -> dict:
    image = ImageInput(filename=filename, content_type=content_type, data=data)
    return get_provider().diagnose(image)


def answer_followup(question: str, context: Optional[dict] = None) -> str:
    return get_provider().answer_followup(question, context)
