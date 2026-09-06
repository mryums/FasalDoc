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


class TranscriptionResponse(BaseModel):
    transcript_urdu: str = Field(min_length=1)


class SpeechSynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


class SpeechSynthesisResponse(BaseModel):
    audio_format: str = "wav"


class HealthResponse(BaseModel):
    provider: str
    configured: bool
    mode: str
    models: dict[str, str]
    configuration_status: str


class ErrorResponse(BaseModel):
    code: str
    detail: str
