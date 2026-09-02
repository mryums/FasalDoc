---
kind: error_handling
name: FastAPI HTTPException + Frontend ApiError — Centralized Error Handling for Diagnosis API
category: error_handling
scope:
    - '**'
source_files:
    - backend/main.py
    - backend/routes/diagnose.py
    - backend/routes/followup.py
    - backend/services/diagnosis_service.py
    - backend/utils/validators.py
    - frontend/src/services/api.ts
    - frontend/src/components/ErrorMessage.tsx
    - tests/test_api.py
---

## Overview

FasalDoc uses a two-layer error-handling strategy: the FastAPI backend raises `fastapi.HTTPException` with explicit status codes and user-facing messages, while the React frontend wraps network failures in a typed `ApiError` class that distinguishes validation, network, and server errors. There is no custom exception hierarchy on the backend; all business and infrastructure errors funnel through FastAPI's built-in exception mechanism.

## Backend (FastAPI)

### Where errors are raised
- **Route-level validation** — `backend/routes/diagnose.py` raises `HTTPException(status_code=400, detail=...)` for disallowed image types, empty uploads, and oversized images (>10 MB). `backend/routes/followup.py` raises the same for empty/whitespace-only questions.
- **Missing fields** — FastAPI's Pydantic request body validation automatically returns `422 Unprocessable Entity` when required fields are absent (verified by `tests/test_api.py::test_ask_followup_missing_question_is_422`).
- **Unhandled exceptions** — Both `/diagnose` and `/ask-followup` wrap service calls in `try/except Exception` blocks that catch any unexpected failure and re-raise as `HTTPException(status_code=500, detail="... try again later.")`. The comment explicitly states the intent: "Never leak internal/AI errors to the client." `HTTPException` instances are re-raised unchanged so they pass through to FastAPI's default handler.

### Service layer isolation
`backend/services/diagnosis_service.py` defines a `DiagnosisProvider` Protocol and a `MockDiagnosisProvider`. When no `DASHSCOPE_API_KEY` is configured (or construction fails), it falls back to the mock via `_build_provider()`, which logs a warning instead of raising. This means AI-provider failures are swallowed at the service boundary and surfaced upstream only if the route wrapper catches them.

### Validation helpers
`backend/utils/validators.py` exposes pure boolean validators (`validate_image_type`, `validate_image_size`, `validate_question`) used exclusively by routes to decide whether to raise `HTTPException`. No exceptions are raised from validators themselves.

### Middleware
Only CORS middleware is registered (`CORSMiddleware` in `backend/main.py`); there is no global exception handler or custom middleware for error normalization.

## Frontend (React / TypeScript)

### Centralized API client
`frontend/src/services/api.ts` is the single entry point for all backend calls. It:
- Defines `ApiError extends Error` with a `kind` field of type `'validation' | 'network' | 'server'` and an optional `status` code.
- Mirrors backend validation constants (`ALLOWED_IMAGE_TYPES`, `MAX_IMAGE_SIZE`) and provides `validateImageFile` / `validateQuestion` for early client-side rejection before any network call.
- Parses non-OK responses via `parseBackendError`, which reads `response.detail` (the FastAPI convention) and maps 400/422 to `ApiError('validation', ...)` and everything else to `ApiError('server', ...)`. Network failures (`fetch` throws) become `ApiError('', 'network')`.

### UI presentation
`frontend/src/components/ErrorMessage.tsx` renders a reusable alert box with an icon, the message, and an optional retry button. It consumes i18n translations via `useLanguage()` and uses `role="alert"` for accessibility. Components consume `ApiError.kind` to choose between showing a retry action (network/server) versus inline validation feedback.

## Tests as enforcement
`tests/test_api.py` asserts the expected error surface:
- 400 for invalid file type, empty image, too-large image, whitespace-only question.
- 422 for missing required fields.
- 200 for valid requests.
- CORS headers present for the dev origin.
- Service fallback to `MockDiagnosisProvider` when credentials are absent.

## Conventions observed
1. **User-facing errors are always `HTTPException` with a plain `detail` string** — never raw Python tracebacks or internal objects.
2. **Client input is validated twice**: once in the frontend (`api.ts`) for immediate UX, and again in the backend (`validators.py` → routes) for safety.
3. **Unexpected exceptions are caught at the route boundary** and converted to a generic 500 response; internal stack traces are logged (service layer) but never exposed.
4. **AI provider failures degrade gracefully** — the service layer logs a warning and returns deterministic mock data rather than failing the request.
5. **Frontend errors are typed** — `ApiErrorKind` discriminates between client-side validation, network loss, and server errors, enabling consistent UI behavior.