---
kind: build_system
name: FasalDoc Build & Deployment (Vite + FastAPI + Render)
category: build_system
scope:
    - '**'
source_files:
    - requirements.txt
    - frontend/package.json
    - frontend/vite.config.ts
    - demo_backup/render.yaml
    - tests/test_api.py
---

## What system/approach is used

The project uses a simple, scriptless monorepo build and deployment approach:
- **Backend**: Python/FastAPI with dependency pinning via `requirements.txt`. The server is started directly with `uvicorn`.
- **Frontend**: React/TypeScript SPA built with **Vite** (`vite build`), typed via TypeScript (`tsc -b`) before bundling.
- **Testing**: Pytest runs against the FastAPI app using `fastapi.testclient.TestClient`; no external network calls are made during tests.
- **Deployment**: A single Render platform configuration (`demo_backup/render.yaml`) defines how the backend is built and served. There is no Dockerfile, Makefile, CI pipeline, or release automation in this repository.

## Key files and packages

- `requirements.txt` — declares backend dependencies: `fastapi`, `uvicorn`, `python-multipart`, `pytest`, `httpx`.
- `frontend/package.json` — declares frontend dependencies and scripts (`dev`, `build`, `preview`).
- `frontend/vite.config.ts` — Vite config enabling the React plugin and setting the dev server to port `5173`.
- `demo_backup/render.yaml` — Render service definition that installs requirements and starts `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
- `tests/test_api.py` — pytest suite exercising `/`, `/diagnose`, `/ask-followup`, OpenAPI docs, CORS, and the mock provider fallback.

## Architecture and conventions

- **Two independent build targets**: the backend and frontend have separate dependency manifests and build commands; there is no top-level orchestrator tying them together.
- **Dev workflow implied by scripts/configs**:
  - Backend: `pip install -r requirements.txt` then `uvicorn backend.main:app --host 0.0.0.0 --port <port>`.
  - Frontend: `npm run dev` (Vite on port 5173) and `npm run build` (type-check then bundle).
- **Environment variables**: `.env.example` exists at the repo root; the backend relies on an optional `DASHSCOPE_API_KEY` environment variable to switch between a real AI provider and a deterministic mock (verified by tests). No other env-driven build flags were found.
- **CORS convention**: the backend explicitly allows the local Vite dev origin `http://localhost:5173`, matching the Vite dev server port configured in `vite.config.ts`.
- **Test isolation**: all tests use `TestClient` and assert offline behavior; they never hit external services, which keeps the test step self-contained.

## Conventions and constraints

- **Dependency management**: pinned ranges in `requirements.txt` (e.g. `fastapi>=0.111,<1.0`, `uvicorn>=0.30,<1.0`) constrain major versions while allowing patch/minor updates.
- **Frontend build contract**: `npm run build` first runs `tsc -b` (project-referenced TypeScript build) and then `vite build`; both must succeed for a production bundle to be emitted.
- **Render deployment contract**: the only deployment artifact is `demo_backup/render.yaml`, which instructs Render to install from `requirements.txt` and start the Uvicorn ASGI application bound to `$PORT` on `0.0.0.0`.
- **No containerization**: there is no `Dockerfile` or `docker-compose.yml` in the repository; deployment is done via Render's native Python runtime.
- **No CI/CD**: there is no `.github/workflows`, `Jenkinsfile`, GitLab CI, or similar pipeline file; automated testing and builds are not defined in this repo.
- **No Makefile or shell build scripts**: build steps are delegated entirely to npm/Vite and pip/uvicorn invocations referenced by the Render config.