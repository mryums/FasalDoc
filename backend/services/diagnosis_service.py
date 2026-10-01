"""Diagnosis service layer (M2 backend).

This module defines the contract between the FastAPI routes and the AI
backend. Routes call the module-level helpers (:func:`run_diagnosis` and
:func:`answer_followup`); they never hardcode AI logic.

Provider priority: Qwen (Member 1) -> Gemini -> offline Mock.

Plugging in a real AI provider:
    1. Create a ``backend/services/<name>_provider.py`` exposing a factory::

           def create_provider() -> "DiagnosisProvider":
               ...

       whose object implements the :class:`DiagnosisProvider` protocol below.
    2. Set the provider's API key in the environment:
           - ``DASHSCOPE_API_KEY``  -> Qwen / Alibaba Cloud (tried first)
           - ``GEMINI_API_KEY``     -> Gemini 2.5 Flash (tried second)

Nothing in the routes needs to change. If credentials for a provider are
missing, or that provider cannot be built/queried, the service transparently
falls back to the next one in line, ending with the offline
:class:`MockDiagnosisProvider`, so the app keeps working without any cloud
AI access.
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
    question: Optional[str] = None
    # Selected UI language ('en' | 'ur' | 'rom'); providers that support
    # localized answers (Gemini) honor it, others simply ignore it.
    language: Optional[str] = None


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

    Provider priority: Qwen (Member 1) -> Gemini -> offline Mock.

    Prefers Member 1's real provider when credentials exist; otherwise, if a
    real Gemini API key is configured, uses Gemini 2.5 Flash (vision + text)
    as the AI provider. If neither is configured, or construction of either
    fails for any reason, safely falls back to the offline mock so the app
    keeps working without any cloud AI access.
    """
    if _looks_configured(os.getenv("DASHSCOPE_API_KEY", "")):
        try:
            from backend.services.qwen_provider import create_provider  # type: ignore

            return create_provider()
        except Exception as exc:  # pragma: no cover - depends on Member 1's module
            logger.warning(
                "Qwen provider unavailable (%s); trying Gemini/mock fallback.", exc
            )

    if _looks_configured(os.getenv("GEMINI_API_KEY", "")):
        try:
            from backend.services.gemini_provider import create_provider  # type: ignore

            return create_provider()
        except Exception as exc:
            logger.warning(
                "Gemini provider unavailable (%s); using offline mock fallback.", exc
            )

    return MockDiagnosisProvider()


_provider: Optional[DiagnosisProvider] = None
_latest_context: Optional[dict] = None


def get_provider() -> DiagnosisProvider:
    global _provider
    if _provider is None:
        _provider = _build_provider()
    return _provider


def get_latest_context() -> Optional[dict]:
    """Retrieve the current in-memory session context from the last diagnosis."""
    return _latest_context


def set_latest_context(context: Optional[dict]) -> None:
    """Update the in-memory session context."""
    global _latest_context
    _latest_context = context


def clear_context() -> None:
    """Clear the stored session context."""
    global _latest_context
    _latest_context = None


def reset_provider() -> None:
    """Clear the cached provider and session context. Intended for tests / runtime reconfiguration."""
    global _provider, _latest_context
    _provider = None
    _latest_context = None


# --- Helpers used by the routes -------------------------------------------

def run_diagnosis(
    filename: str,
    *,
    data: bytes = b"",
    content_type: str = "image/jpeg",
    question: Optional[str] = None,
    language: Optional[str] = None,
) -> dict:
    image = ImageInput(
        filename=filename, content_type=content_type, data=data,
        question=question, language=language,
    )
    result = get_provider().diagnose(image)
    context = {
        "diagnosis": result.get("diagnosis"),
        "confidence": result.get("confidence"),
        "advice": result.get("advice"),
        "needs_expert": result.get("needs_expert"),
        "original_question": question,
    }
    if language is not None:
        # Only carried when the client sends one — keeps the no-language
        # context shape identical to before.
        context["language"] = language
    set_latest_context(context)
    return result


def answer_followup(
    question: str,
    context: Optional[dict] = None,
    language: Optional[str] = None,
) -> str:
    if context is None:
        context = get_latest_context()
    if language is not None:
        # Carry the selected language without mutating the stored context.
        context = {**(context or {}), "language": language}
    return get_provider().answer_followup(question, context)

