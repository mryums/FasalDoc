from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from backend.models import SpeechSynthesisRequest, TranscriptionResponse
from backend.services import diagnosis_service
from backend.services.ai_config import get_settings
from backend.services.ai_errors import AIInvalidModelOutputError
from backend.utils.validators import (
    detect_audio_format,
    validate_audio_size,
    validate_audio_type,
    validate_tts_text,
)


router = APIRouter()


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(audio: UploadFile = File(...)):
    if not validate_audio_type(audio.content_type):
        raise HTTPException(status_code=400, detail="Only supported audio files are allowed.")

    audio_data = await audio.read()
    if not validate_audio_size(len(audio_data)):
        raise HTTPException(status_code=400, detail="Audio must be smaller than 10 MB.")

    audio_format = detect_audio_format(audio_data)
    if not audio_format:
        raise HTTPException(status_code=400, detail="Audio content is not a supported valid format.")

    result = diagnosis_service.transcribe_audio(audio_data, audio_format)
    transcript = result.get("transcript_urdu", "")
    if not isinstance(transcript, str) or not transcript.strip():
        raise AIInvalidModelOutputError()
    return TranscriptionResponse(transcript_urdu=" ".join(transcript.split()))


@router.post(
    "/speak",
    response_class=Response,
    responses={200: {"content": {"audio/wav": {}}}},
)
async def speak(payload: SpeechSynthesisRequest):
    if not validate_tts_text(payload.text, get_settings().tts_max_length):
        raise HTTPException(status_code=400, detail="Text must be non-empty and within the configured length limit.")

    result = diagnosis_service.synthesize_speech(payload.text.strip())
    audio_bytes = result.get("audio_bytes")
    if not isinstance(audio_bytes, bytes) or not audio_bytes:
        raise AIInvalidModelOutputError()
    return Response(content=audio_bytes, media_type="audio/wav")
