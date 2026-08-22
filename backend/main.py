from fastapi import FastAPI
from backend.routes.diagnose import router as diagnose_router
from backend.routes.followup import router as followup_router

app = FastAPI(title="FasalDoc API")

app.include_router(diagnose_router)
app.include_router(followup_router)

@app.get("/")
def home():
    return {
        "message": "FasalDoc API is running"
    }
