# FasalDoc

Crop-disease diagnosis assistant: a FastAPI backend (M2) serving a React/Vite
frontend. The backend runs **fully offline on mock AI responses** until the
real Qwen / Alibaba Cloud layer (Member 1) is configured.

## Repository layout

```
backend/        FastAPI app (routes, models, service layer, validators)
frontend/       React + Vite single-page app (Member 3)
tests/          Offline pytest suite (no network / AI calls)
requirements.txt
.env.example    Configuration template (placeholders only — no secrets)
```

## Prerequisites

- Python 3.10+
- Node.js 18+ (only needed to run the frontend)

## Backend (M2)

### 1. Create and activate a virtual environment

```bash
# from the repository root
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows (PowerShell/cmd)
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure (optional)

```bash
cp .env.example .env
```

- Leave `DASHSCOPE_API_KEY` blank (or as the placeholder) to stay offline on
  mock responses.
- `CORS_ALLOW_ORIGINS` defaults to the Vite dev server
  (`http://localhost:5173,http://127.0.0.1:5173`).

### 4. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

- API:      http://localhost:8000
- Swagger:  http://localhost:8000/docs
- OpenAPI:  http://localhost:8000/openapi.json

### 5. Run the tests

```bash
pytest
```

All tests run offline using FastAPI's `TestClient` and never call any external
or AI service.

## Frontend (Member 3)

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
```

The frontend reads the backend URL from `VITE_API_BASE_URL`
(default `http://localhost:8000`). Start the backend first.

## Endpoints

| Method | Path             | Purpose                                   |
|--------|------------------|-------------------------------------------|
| GET    | `/`              | Health check                              |
| POST   | `/diagnose`      | Multipart image upload -> diagnosis       |
| POST   | `/ask-followup`  | JSON `{ "question" }` -> follow-up answer |

## AI integration (Member 1) — how to plug in Qwen/Alibaba Cloud

Real AI is **not** implemented here and requires Alibaba Cloud / DashScope
credentials that M2 does not have. The integration point is isolated:

1. Implement `backend/services/qwen_provider.py` exposing
   `create_provider()` that returns an object satisfying the
   `DiagnosisProvider` protocol in `backend/services/diagnosis_service.py`
   (`diagnose(image)` and `answer_followup(question, context)`).
2. Set `DASHSCOPE_API_KEY` (plus `DASHSCOPE_BASE_URL` / `DASHSCOPE_MODEL`).
3. **No route changes are required.** Until a key is present or the provider
   can be built, the app transparently falls back to the offline mock.

## Remaining M2 blockers

- Real Qwen/Alibaba Cloud AI calls (owned by Member 1; needs credentials).
- Any audio/transcription endpoint (only relevant if frontend adds voice input
  later — currently out of M2 scope).
