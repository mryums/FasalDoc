from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.models import DiagnosisResponse
from backend.services import diagnosis_service
from backend.utils.validators import (
    validate_image_type,
    validate_image_size
)

router = APIRouter()


@router.post(
    "/diagnose",
    response_model=DiagnosisResponse,
    summary="Diagnose a crop disease from an uploaded image",
    tags=["diagnosis"],
)
async def diagnose(
    image: UploadFile = File(...),
    question: Optional[str] = Form(None),
):

    # 1. Check image type
    if not validate_image_type(image.content_type):
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WEBP images are allowed."
        )

    # 2. Read image
    image_data = await image.read()

    # 3. Reject empty uploads early
    if not image_data:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    # 4. Check image size
    if not validate_image_size(len(image_data)):
        raise HTTPException(
            status_code=400,
            detail="Image must be smaller than 10 MB."
        )

    clean_question = question.strip() if question and question.strip() else None

    # 5. Delegate to the diagnosis service (mock offline, real AI later)
    try:
        return diagnosis_service.run_diagnosis(
            image.filename,
            data=image_data,
            content_type=image.content_type,
            question=clean_question,
        )
    except HTTPException:
        raise
    except Exception:
        # Never leak internal/AI errors to the client.
        raise HTTPException(
            status_code=500,
            detail="Diagnosis failed. Please try again later."
        )