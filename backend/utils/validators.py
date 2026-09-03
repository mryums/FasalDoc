ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_image_type(content_type: str) -> bool:
    return content_type in ALLOWED_IMAGE_TYPES


def validate_image_size(file_size: int) -> bool:
    return 0 < file_size <= MAX_IMAGE_SIZE


def validate_question(question: str) -> bool:
    return bool(question and question.strip())