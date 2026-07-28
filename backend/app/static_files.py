"""Optional static frontend mount for production Docker / Railway."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RESERVED_PREFIXES = ("api/", "docs", "openapi.json", "redoc")


def resolve_static_dir(static_dir_setting: str) -> Path | None:
    """Pick built frontend directory: explicit STATIC_DIR, frontend/dist, or /app/static."""
    candidates: list[Path] = []
    if static_dir_setting.strip():
        candidates.append(Path(static_dir_setting).expanduser())

    # backend/app/static_files.py -> repo root is parents[2]
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / "frontend" / "dist")
    candidates.append(Path("/app/static"))

    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_dir() and (resolved / "index.html").is_file():
            return resolved
    return None


def _resolve_static_file(static_dir: Path, full_path: str) -> Path | None:
    candidate = (static_dir / full_path).resolve()
    static_root = static_dir.resolve()
    if not str(candidate).startswith(str(static_root)):
        return None
    if candidate.is_file():
        return candidate
    return None


def mount_frontend(app: FastAPI, static_dir: Path) -> None:
    if not static_dir.is_dir():
        return

    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def serve_index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        if full_path.startswith(RESERVED_PREFIXES):
            raise HTTPException(status_code=404, detail="Not found")
        static_file = _resolve_static_file(static_dir, full_path)
        if static_file is not None:
            return FileResponse(static_file)
        return FileResponse(static_dir / "index.html")
