from pathlib import Path


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
IMAGE_FORMATS = {
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
}
ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/webm",
    "audio/ogg",
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_AUDIO_SIZE = 10 * 1024 * 1024
MAX_QUESTION_LENGTH = 1000
DEFAULT_TTS_MAX_LENGTH = 1500


def normalize_content_type(content_type: str | None) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def validate_image_type(content_type: str | None) -> bool:
    return normalize_content_type(content_type) in ALLOWED_IMAGE_TYPES


def image_format_from_mime(content_type: str | None) -> str | None:
    return IMAGE_FORMATS.get(normalize_content_type(content_type))


def validate_image_size(file_size: int) -> bool:
    return 0 < file_size <= MAX_IMAGE_SIZE


def validate_question(question: str | None, max_length: int = MAX_QUESTION_LENGTH) -> bool:
    return bool(question and question.strip() and len(question.strip()) <= max_length)


def validate_audio_type(content_type: str | None) -> bool:
    return normalize_content_type(content_type) in ALLOWED_AUDIO_TYPES


def validate_audio_size(file_size: int) -> bool:
    return 0 < file_size <= MAX_AUDIO_SIZE


def detect_audio_format(audio_bytes: bytes) -> str | None:
    if len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return "wav"
    if audio_bytes.startswith(b"ID3") or (
        len(audio_bytes) >= 2 and audio_bytes[0] == 0xFF and audio_bytes[1] & 0xE0 == 0xE0
    ):
        return "mp3"
    if len(audio_bytes) >= 12 and audio_bytes[4:8] == b"ftyp":
        return "m4a"
    if audio_bytes.startswith(b"\x1aE\xdf\xa3"):
        return "webm"
    if audio_bytes.startswith(b"OggS"):
        return "ogg"
    return None


def validate_tts_text(text: str | None, max_length: int = DEFAULT_TTS_MAX_LENGTH) -> bool:
    return bool(text and text.strip() and len(text.strip()) <= max_length)


def safe_filename(filename: str | None) -> str:
    name = Path(filename or "").name.strip()
    return name[:255] if name and name not in {".", ".."} else "upload"
