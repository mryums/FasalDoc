from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.diagnose import router as diagnose_router
from backend.routes.followup import router as followup_router

app = FastAPI(title="FasalDoc API")

# Development-friendly CORS so the local frontend can call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnose_router)
app.include_router(followup_router)

@app.get("/")
def home():
    return {
        "message": "FasalDoc API is running"
    }
