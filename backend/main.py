import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.diagnose import router as diagnose_router
from backend.routes.followup import router as followup_router

app = FastAPI(
    title="FasalDoc API",
    description=(
        "Backend for FasalDoc: crop-disease diagnosis and follow-up Q&A. "
        "Runs fully offline with mock responses until the real Qwen/Alibaba "
        "Cloud AI layer (Member 1) is configured via environment variables."
    ),
    version="1.0.0",
)

# CORS for local frontend development.
# Defaults to the Vite dev server; override with CORS_ALLOW_ORIGINS
# (comma-separated) for other environments.
_DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
allow_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnose_router)
app.include_router(followup_router)

@app.get("/", tags=["health"])
def home():
    return {
        "message": "FasalDoc API is running"
    }
