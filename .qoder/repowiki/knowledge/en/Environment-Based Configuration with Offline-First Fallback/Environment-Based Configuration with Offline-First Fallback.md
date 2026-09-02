---
kind: configuration_system
name: Environment-Based Configuration with Offline-First Fallback
category: configuration_system
scope:
    - '**'
source_files:
    - .env.example
    - backend/main.py
    - backend/services/diagnosis_service.py
    - frontend/src/services/api.ts
    - frontend/src/vite-env.d.ts
    - frontend/vite.config.ts
    - demo_backup/render.yaml
---

## What system/approach is used

FasalDoc uses a minimal, environment-variable-driven configuration approach. There is no dedicated config library (no Pydantic `Settings`, no YAML/TOML parser, no `python-dotenv` loader). Instead, the backend reads values directly via `os.getenv`, and the frontend reads Vite build-time env vars via `import.meta.env`. A single `.env.example` template documents every supported variable, and deployment is driven by a Render `render.yaml` that injects runtime env.

The key architectural decision is **offline-first**: when no AI provider credentials are configured, the backend transparently falls back to a deterministic mock provider so the entire app (routes, tests, demo) runs without network access.

## Key files and packages

- `.env.example` — the single source of truth for all configurable keys (`DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL`, `DASHSCOPE_MODEL`, `BACKEND_PORT`, `CORS_ALLOW_ORIGINS`, `VITE_API_BASE_URL`). The file explicitly states it is a template only; real `.env` is gitignored.
- `backend/main.py` — FastAPI app bootstrap. Reads `CORS_ALLOW_ORIGINS` from `os.getenv` with a hard-coded default of `http://localhost:5173,http://127.0.0.1:5173` and applies it to `CORSMiddleware`.
- `backend/services/diagnosis_service.py` — holds the provider selection logic. `_looks_configured()` treats empty strings and the placeholder value `your_key_here` as unconfigured. `_build_provider()` lazily tries to import `backend.services.qwen_provider.create_provider()` only when `DASHSCOPE_API_KEY` is present and non-placeholder; any exception triggers a logged warning and fallback to `MockDiagnosisProvider`. A module-level `_provider` cache plus `reset_provider()` enables test-time reconfiguration.
- `frontend/src/services/api.ts` — central API client. Derives `API_BASE` from `import.meta.env.VITE_API_BASE_URL` with a default of `http://localhost:8000`; strips trailing slashes. All component calls go through this file, never via raw `fetch` scattered across components.
- `frontend/src/vite-env.d.ts` — declares the `readonly VITE_API_BASE_URL?: string` type so TypeScript knows about the Vite-injected var.
- `frontend/vite.config.ts` — hard-codes the dev server port `5173`; no external config file is used.
- `demo_backup/render.yaml` — Render deployment manifest. Sets `env: python`, installs `requirements.txt`, and starts uvicorn on `$PORT` (Render-provided), demonstrating how production env is injected at deploy time.

## Architecture and conventions

1. **Single env-var surface area.** Every tunable setting is documented in `.env.example` and consumed via `os.getenv` / `import.meta.env`. There is no layered config (no defaults file + override file pattern).
2. **Hard-coded defaults everywhere.** If an env var is absent, sensible defaults are applied inline:
   - CORS origins default to Vite's dev server addresses.
   - Frontend API base URL defaults to `http://localhost:8000`.
   - Backend port defaults to `8000` (per the comment in `.env.example` and uvicorn invocation).
3. **Offline-first provider resolution.** The diagnosis service checks `DASHSCOPE_API_KEY` at first use. If missing or equal to the placeholder `your_key_here`, it returns `MockDiagnosisProvider`, which produces fixed responses (`Early Blight`, confidence `0.70`, advice text). This lets developers run the full stack without cloud credentials.
4. **Secrets stay server-side.** The `.env.example` header and `api.ts` comments explicitly state that AI/cloud credentials must never be exposed to the browser; the frontend only knows the backend base URL.
5. **Frontend-backend contract duplication is intentional.** `api.ts` mirrors `backend/utils/validators.py` (allowed image types, max size, question validation) so the UI can fail fast before sending requests. This is a configuration/validation convention rather than shared code.
6. **Deployment env is separate from dev env.** Local development uses `.env` (gitignored); production uses Render's `render.yaml` to inject `PORT` and any other secrets at deploy time.

## Conventions and constraints

- **All secrets live in `.env` (or platform secret stores).** The `.env.example` header instructs copying to `.env` and keeping it out of version control; `.gitignore` enforces this.
- **AI provider activation is opt-in via env var presence.** The backend does not error if `DASHSCOPE_API_KEY` is missing — it silently uses the mock. Only when the key is present and non-placeholder does it attempt the real provider.
- **CORS origins are comma-separated env strings parsed at startup.** `backend/main.py` splits `CORS_ALLOW_ORIGINS` on commas and strips whitespace; malformed entries are ignored.
- **Frontend env vars must be prefixed with `VITE_`.** `VITE_API_BASE_URL` follows Vite's convention and is declared in `vite-env.d.ts` for type safety.
- **No config migration or schema validation exists.** Values are read as raw strings and split/parsed inline where needed; there is no centralized settings model that validates types or required fields.
- **Provider factory is pluggable but optional.** The docstring in `diagnosis_service.py` prescribes the shape of a future `qwen_provider.py` (`create_provider() -> DiagnosisProvider`), but the module works fully without it.