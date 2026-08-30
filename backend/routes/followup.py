from fastapi import APIRouter, HTTPException

from backend.models import FollowupRequest, FollowupResponse
from backend.services import diagnosis_service
from backend.utils.validators import validate_question

router = APIRouter()


@router.post(
    "/ask-followup",
    response_model=FollowupResponse,
    summary="Ask a follow-up question about a diagnosis",
    tags=["followup"],
)
async def ask_followup(payload: FollowupRequest):

    # Reject empty/whitespace-only questions
    if not validate_question(payload.question):
        raise HTTPException(
            status_code=400,
            detail="Question must not be empty."
        )

    # Delegate to the diagnosis service (mock offline, real AI later)
    try:
        answer = diagnosis_service.answer_followup(payload.question)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Follow-up answer failed. Please try again later."
        )

    return {
        "question": payload.question,
        "answer": answer,
    }
