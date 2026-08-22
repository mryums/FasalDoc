from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.post("/diagnose")
async def diagnose(image: UploadFile = File(...)):
    return {
        "filename": image.filename,
        "content_type": image.content_type,
        "diagnosis": "Early Blight",
        "confidence": 0.70,
        "advice": "Remove affected leaves and improve airflow around the plant."
    }