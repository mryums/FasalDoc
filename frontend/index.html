# FasalDoc — Frontend (Member 3)

AI-assisted crop disease diagnosis for Pakistani farmers.
Upload a crop photo → get an understandable diagnosis with confidence and a recommended action → ask follow-up questions.

This frontend is built strictly against **Member 2's FastAPI contract** (see "Backend contract" below). No backend files were modified.

## Stack

- Vite 7 + React 19 + TypeScript (strict)
- No UI framework — hand-rolled CSS with design tokens (`src/styles/tokens.css`)
- i18n: English / Urdu (RTL) / Roman Urdu (`src/i18n/`)

## Run

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check + production build
```

The backend base URL comes from `VITE_API_BASE_URL` (see `.env.example`), defaulting to `http://localhost:8000`. No AI/cloud credentials ever live in the frontend — architecture is Frontend → FastAPI → AI service.

> This machine had no Node.js installed; a portable Node v22 LTS lives in `.tools/node-v22.21.1-win-x64`. Add it to PATH (`set PATH=%CD%\.tools\node-v22.21.1-win-x64;%PATH%`) or install Node normally.

### Testing without the real backend

A contract-mirror stub (test harness only, not part of the product) is at
`%TEMP%\fasaldoc-stub\stub_server.py` — `python stub_server.py` serves the same routes, validation messages and mock payload on port 8000. Test fixtures (valid/invalid/oversized/force500 images) are in `%TEMP%\fasaldoc-stub\test-assets`.

## Backend contract consumed (source of truth: Member 2)

| Route | Request | Response |
|---|---|---|
| `GET /` | – | `{ message }` |
| `POST /diagnose` | multipart form, field **`image`** (JPEG/PNG/WEBP, ≤ 10 MB) | `DiagnosisResponse { filename, diagnosis, confidence (0–1), advice, needs_expert }` |
| `POST /ask-followup` | JSON `FollowupRequest { question }` (non-empty) | `FollowupResponse { question, answer }` |

Frontend mirrors: `src/types/api.ts` (models), `src/services/api.ts` (single API layer), client-side validation in `validateImageFile`/`validateQuestion` matches `backend/utils/validators.py` exactly (same limits, same user-facing messages as the backend's 400 details).

## Frontend architecture

```
src/
  services/api.ts        centralized fetch layer (no fetch in components)
  types/api.ts           TS mirrors of backend Pydantic models
  i18n/                  en / ur (RTL) / rom translations + LanguageContext
  data/agriculture.ts    Member 4 dataset integration point (currently empty)
  components/            Navbar, ImageUploader, QuestionInput (voice-ready),
                         ConfidenceIndicator, FollowUpChat, ErrorMessage, ...
  pages/                 Home, Upload, Analyzing, Result, FollowUp screens
  App.tsx                flow state machine (reducer): upload → analyzing →
                         result → followup, with idle/loading/success/error states
```

Voice-ready: `QuestionInput` exposes a `trailing` slot; today it renders a disabled mic placeholder, a future `VoiceInput` can slot in without touching the diagnosis flow.

## Mismatches & coordination notes (frontend adapted, backend untouched)

1. **`/diagnose` accepts no farmer question.** The product flow includes an optional question field. The frontend keeps the question client-side and pre-fills it into the follow-up composer so the farmer never re-types it. If Member 2 adds an optional `question` field to `/diagnose`, wire it in `services/api.ts` (`diagnoseImage`) only.
2. **Response has no `crop` / `symptoms` / `prevention` fields.** The result screen renders only fields that exist in `DiagnosisResponse` (diagnosis, confidence, advice, needs_expert). When Member 2/Member 1 extend the response, add the fields to `types/api.ts` and `ResultScreen` — the card layout already has slots for them.
3. **Member 4's agriculture dataset was not present in the repository.** Nothing agricultural is invented; `src/data/agriculture.ts` is the single integration point (supported crops, tips, Urdu terminology) and the home screen renders crop chips automatically once data is filled in.
4. **Backend AI layer is currently mocked** (`diagnosis_service.py`). The frontend needs no change when the real Qwen service lands; low-confidence handling (uncertainty messaging, expert referral via `needs_expert`) is already in place.

## Verified in-browser

Home → upload (choose/camera/drag-drop) → client validation (type/size/no-image) → analyzing state → result (confidence ring + uncertainty messaging) → follow-up chat (context banner, pre-filled question) → Urdu RTL + Roman Urdu → network/server error states with retry.
