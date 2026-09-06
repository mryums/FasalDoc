from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.models import DiagnosisResponse
from backend.services import diagnosis_service
from backend.utils.validators import (
    MAX_QUESTION_LENGTH,
    safe_filename,
    validate_image_size,
    validate_image_type,
)


router = APIRouter()


@router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose(
    image: UploadFile = File(...),
    question: str | None = Form(default=None, max_length=MAX_QUESTION_LENGTH),
):
    if not validate_image_type(image.content_type):
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WEBP images are allowed.")

    image_data = await image.read()
    if not validate_image_size(len(image_data)):
        raise HTTPException(status_code=400, detail="Image must be smaller than 10 MB.")

    return diagnosis_service.run_diagnosis(
        safe_filename(image.filename),
        data=image_data,
        content_type=image.content_type,
        question=question.strip() if question and question.strip() else None,
    )
