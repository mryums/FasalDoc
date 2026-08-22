from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.utils.validators import (
    validate_image_type,
    validate_image_size
)

router = APIRouter()


@router.post("/diagnose")
async def diagnose(image: UploadFile = File(...)):

    # 1. Check image type
    if not validate_image_type(image.content_type):
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WEBP images are allowed."
        )

    # 2. Read image
    image_data = await image.read()

    # 3. Check image size
    if not validate_image_size(len(image_data)):
        raise HTTPException(
            status_code=400,
            detail="Image must be smaller than 10 MB."
        )

    # 4. Temporary mock response
    return {
        "filename": image.filename,
        "diagnosis": "Early Blight",
        "confidence": 0.70,
        "advice": "Remove affected leaves and improve airflow around the plant.",
        "needs_expert": False
    }