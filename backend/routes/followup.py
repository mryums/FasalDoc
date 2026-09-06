from fastapi import APIRouter, HTTPException

from backend.models import FollowupRequest, FollowupResponse
from backend.services import diagnosis_service
from backend.utils.validators import validate_question

router = APIRouter()


@router.post("/ask-followup", response_model=FollowupResponse)
async def ask_followup(payload: FollowupRequest):

    # Reject empty/whitespace-only questions
    if not validate_question(payload.question):
        raise HTTPException(
            status_code=400,
            detail="Question must not be empty."
        )

    # Temporary mock answer — will be replaced by the Qwen AI service later
    return {
        "question": payload.question,
        "answer": diagnosis_service.answer_followup(payload.question),
    }
