from pydantic import BaseModel, Field


class DiagnosisResponse(BaseModel):
    filename: str
    diagnosis: str
    confidence: float = Field(ge=0, le=1)
    advice: str
    needs_expert: bool


class FollowupRequest(BaseModel):
    question: str = Field(min_length=1)


class FollowupResponse(BaseModel):
    question: str
    answer: str
