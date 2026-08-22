from fastapi import FastAPI
from backend.routes.diagnose import router as diagnose_router

app = FastAPI(title="FasalDoc API")


@app.get("/")
def home():
    return {
        "message": "FasalDoc API is running"
    }


app.include_router(diagnose_router)