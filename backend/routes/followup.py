from fastapi import APIRouter

router = APIRouter()


@router.post("/ask-followup")
async def ask_followup(question: str):
    return {
        "question": question,
        "answer": "This is a temporary response. AI integration will be added later."
    }