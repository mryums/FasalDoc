from fastapi import APIRouter

router = APIRouter()


@router.post("/diagnose")
def diagnose():
    return {
        "diagnosis": "Early Blight",
        "confidence": 0.70,
        "advice": "Remove affected leaves and improve airflow around the plant."
    }