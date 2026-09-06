from fastapi import APIRouter

from backend.models import HealthResponse
from backend.services.ai_config import get_settings


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(**get_settings().diagnostics())
