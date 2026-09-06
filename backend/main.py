from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routes.diagnose import router as diagnose_router
from backend.routes.followup import router as followup_router
from backend.routes.health import router as health_router
from backend.routes.voice import router as voice_router
from backend.services.ai_config import get_cors_origins
from backend.services.ai_errors import AIServiceError


app = FastAPI(title="FasalDoc API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AIServiceError)
async def ai_service_error_handler(_: Request, error: AIServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"code": error.code, "detail": error.public_message},
    )


app.include_router(diagnose_router)
app.include_router(followup_router)
app.include_router(voice_router)
app.include_router(health_router)


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "FasalDoc API is running"}
