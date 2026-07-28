# Stage 01 Bootstrap Report

## Planned scope

- prepare the correctly named project root
- initialize git and local Python environment
- create the first repository structure
- add environment template and initial docs

## Implementation

- Created a new correctly named project root at `D:\CursorProjects\promocode-checker`.
- Initialized a git repository and set the primary branch to `develop`.
- Created a local Python virtual environment in `.venv`.
- Added the initial monorepo structure for `backend`, `frontend`, `desktop`, `infra`, `docs`, `scripts`, `tests`, and `config`.
- Added the first backend bootstrap files:
  - `pyproject.toml`
  - `backend/app/core/config.py`
  - `backend/app/main.py`
  - `tests/backend/test_healthcheck.py`
- Added repository bootstrap files and documentation:
  - `.gitignore`
  - `.editorconfig`
  - `.env.example`
  - `README.md`
  - `docs/branching.md`
  - `docs/local-development.md`
  - `docs/testing-stages.md`
  - `docs/prompts/project-prompts.md`

## Important note

- The original empty folder `D:\CursorProjects\promocode-chacker` could not be renamed in place because it is currently locked by the active Cursor workspace.
- To avoid blocking development, the actual work has been bootstrapped in `D:\CursorProjects\promocode-checker`.
- If needed, the old empty typo folder can be removed later after the workspace/session is switched away from it.

## Tests

- `python --version` -> `Python 3.11.0`
- `python -m pip install -e .[dev] --trusted-host ...` -> success
- `python -m pytest tests/backend/test_healthcheck.py` -> `1 passed`
- `python -m ruff check .` -> passed
- `GET http://127.0.0.1:8000/health` -> `{\"status\":\"ok\",\"app_env\":\"local\",\"app_port\":8000}`

## Review notes

- Stage 1 goal is achieved: the repository now has a clean starting structure, working local Python environment, config bootstrap, and a live FastAPI smoke endpoint.
- The environment install needed a Windows SSL workaround with trusted hosts for PyPI. This should be documented and may need a cleaner long-term fix on the target machine.
- Frontend and Docker scaffolding are intentionally not implemented yet; they belong to later stages.

## Risks and follow-ups

- Need to decide whether to switch the Cursor workspace itself to `D:\CursorProjects\promocode-checker` before deeper implementation, to avoid confusion with the old typo folder.
- Need a local PostgreSQL instance or Dockerized DB in the next stage for real migrations.
- Need to choose whether frontend scaffolding starts manually or through Vite bootstrap in Stage 2/3.
