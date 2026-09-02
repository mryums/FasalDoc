---
kind: dependency_management
name: Dual-Stack Dependency Management (pip + npm with Lockfiles)
category: dependency_management
scope:
    - '**'
source_files:
    - requirements.txt
    - frontend/package.json
    - frontend/package-lock.json
---

## What system/approach is used

FasalDoc is a monorepo that manages dependencies for two separate stacks independently:

- **Python backend** — uses `pip` with a flat `requirements.txt` at the repository root. Dependencies are declared with loose upper-bound ranges (`>=X,<Y`) to allow minor/patch updates while pinning major versions.
- **React/Vite frontend** — uses `npm` with `package.json` in `frontend/` and a committed `package-lock.json` (lockfileVersion 3) that pins every transitive dependency to an exact version, hash, and integrity digest.

There is no vendoring of Python packages, no private PyPI registry configured, no `go.mod`, no `yarn.lock`, and no monorepo tool (e.g., pnpm workspace, lerna). Each stack installs its own dependency tree from public registries (PyPI and the default npm registry).

## Key files and packages

- `requirements.txt` — declares the backend's runtime and test dependencies: `fastapi`, `uvicorn`, `python-multipart`, `pytest`, `httpx`. All are pinned with `>=X,<1.0` style constraints.
- `frontend/package.json` — declares direct dependencies (`react`, `react-dom`) and dev dependencies (`@types/react`, `@types/react-dom`, `@vitejs/plugin-react`, `typescript`, `vite`).
- `frontend/package-lock.json` — full deterministic lockfile for the frontend dependency graph; committed to the repo so CI and other developers reproduce the same tree.

## Architecture and conventions

- **Separate manifests per language**: Python and JavaScript/TypeScript each have their own manifest file in the conventional location; there is no cross-referencing between them.
- **Loose versioning on Python side**: `requirements.txt` uses caret-style upper bounds (`>=0.111,<1.0`, `>=0.30,<1.0`, etc.) rather than exact pins, which allows automatic patch/minor upgrades but does not guarantee reproducible builds without an external lockfile.
- **Exact pinning on the frontend side**: The npm lockfile records exact resolved versions and SHA integrity hashes for every package, including deep transitive dependencies (e.g., `@babel/*`, `lru-cache`, `semver`), ensuring deterministic installs across environments.
- **No vendoring or private registries**: No `vendor/` directory, no `.pypirc`, no `~/.npmrc` overrides, and no `GOPRIVATE` equivalents exist. All packages resolve from public PyPI and the default npm registry.
- **No shared dependency orchestration**: There is no top-level script that coordinates installing both stacks; each must be installed separately (`pip install -r requirements.txt` and `npm ci` / `npm install` in `frontend/`).

## Conventions and constraints

- Backend dependencies are constrained by major-version ceilings (`<1.0`) in `requirements.txt`, preventing breaking upgrades while allowing semantic-minor bumps.
- Frontend dependencies use `^` (caret) ranges in `package.json`, deferring to the committed `package-lock.json` for the exact resolved versions during install.
- The only lockfile present is `frontend/package-lock.json`; the Python side has no equivalent lockfile checked into version control.
- No private package sources, proxy configuration, or authentication tokens are referenced anywhere in the repository.