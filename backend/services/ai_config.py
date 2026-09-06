import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)

DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_VISION_MODEL = "qwen-vl-plus"
DEFAULT_TEXT_MODEL = "qwen-plus"
DEFAULT_ASR_MODEL = "qwen3-asr-flash"
DEFAULT_TTS_MODEL = "qwen3-tts-flash"
DEFAULT_TTS_VOICE = "Cherry"
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MAX_RETRIES = 2
DEFAULT_TTS_MAX_LENGTH = 1500
DEFAULT_CONFIDENCE_THRESHOLD = 60
DEFAULT_CORS_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")

_PLACEHOLDER_KEYS = {
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


def _clean_value(value: str | None) -> str:
    return (value or "").strip().strip("\"'")


def configured_api_key(value: str | None = None) -> str | None:
    candidate = _clean_value(os.getenv("DASHSCOPE_API_KEY") if value is None else value)
    if not candidate or candidate.lower() in _PLACEHOLDER_KEYS:
        return None
    return candidate


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(_clean_value(os.getenv(name)) or default)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class AISettings:
    api_key: str | None
    base_url: str
    vision_model: str
    text_model: str
    asr_model: str
    tts_model: str
    tts_voice: str
    timeout_seconds: int
    max_retries: int
    tts_max_length: int
    confidence_threshold: int

    @property
    def configured(self) -> bool:
        return self.api_key is not None

    def diagnostics(self) -> dict[str, object]:
        return {
            "provider": "qwen-dashscope" if self.configured else "mock",
            "configured": self.configured,
            "mode": "real" if self.configured else "mock",
            "models": {
                "vision": self.vision_model,
                "text": self.text_model,
                "asr": self.asr_model,
                "tts": self.tts_model,
            },
            "configuration_status": "ready" if self.configured else "missing_api_key",
        }


def get_settings() -> AISettings:
    legacy_model = _clean_value(os.getenv("DASHSCOPE_MODEL"))
    return AISettings(
        api_key=configured_api_key(),
        base_url=_clean_value(os.getenv("DASHSCOPE_BASE_URL")) or DEFAULT_DASHSCOPE_BASE_URL,
        vision_model=_clean_value(os.getenv("DASHSCOPE_VISION_MODEL")) or DEFAULT_VISION_MODEL,
        text_model=_clean_value(os.getenv("DASHSCOPE_TEXT_MODEL")) or legacy_model or DEFAULT_TEXT_MODEL,
        asr_model=_clean_value(os.getenv("DASHSCOPE_ASR_MODEL")) or DEFAULT_ASR_MODEL,
        tts_model=_clean_value(os.getenv("DASHSCOPE_TTS_MODEL")) or DEFAULT_TTS_MODEL,
        tts_voice=_clean_value(os.getenv("DASHSCOPE_TTS_VOICE")) or DEFAULT_TTS_VOICE,
        timeout_seconds=_bounded_int("DASHSCOPE_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS, 1, 300),
        max_retries=_bounded_int("DASHSCOPE_MAX_RETRIES", DEFAULT_MAX_RETRIES, 0, 10),
        tts_max_length=_bounded_int("DASHSCOPE_TTS_MAX_LENGTH", DEFAULT_TTS_MAX_LENGTH, 1, 10000),
        confidence_threshold=_bounded_int(
            "DASHSCOPE_CONFIDENCE_THRESHOLD",
            DEFAULT_CONFIDENCE_THRESHOLD,
            0,
            100,
        ),
    )


def get_cors_origins() -> list[str]:
    raw_origins = _clean_value(os.getenv("CORS_ALLOW_ORIGINS"))
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip() and origin.strip() != "*"]
    return origins or list(DEFAULT_CORS_ORIGINS)
