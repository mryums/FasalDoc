from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.models import DiagnosisResponse
from backend.services import diagnosis_service
from backend.utils.validators import (
    validate_image_type,
    validate_image_size,
)

router = APIRouter()


@router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose(image: UploadFile = File(...)):

    # 1. Validate image type
    if not validate_image_type(image.content_type):
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WEBP images are allowed.",
        )

    # 2. Read uploaded image
    image_data = await image.read()

    # 3. Validate image size
    if not validate_image_size(len(image_data)):
        raise HTTPException(
            status_code=400,
            detail="Image must be smaller than 10 MB.",
        )

    # 4. Send image information to diagnosis service
    return diagnosis_service.run_diagnosis(
        image.filename,
        data=image_data,
        content_type=image.content_type,
    )