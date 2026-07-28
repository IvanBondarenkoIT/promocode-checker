"""Optional static frontend mount for production Docker / Railway."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RESERVED_PREFIXES = ("api/", "docs", "openapi.json", "redoc")


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
        if full_path == "health" or full_path.startswith(RESERVED_PREFIXES):
            raise HTTPException(status_code=404, detail="Not found")
        static_file = _resolve_static_file(static_dir, full_path)
        if static_file is not None:
            return FileResponse(static_file)
        return FileResponse(static_dir / "index.html")
