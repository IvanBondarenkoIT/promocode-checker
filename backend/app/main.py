from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.static_files import mount_frontend, resolve_static_dir

settings = get_settings()

app = FastAPI(
    title="Promocode Checker",
    version="0.1.0",
    summary="Backend API for promo validation, cashier flows, admin tools, and ERP reconciliation.",
)

cors_origins = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    settings.frontend_base_url.rstrip("/"),
}
if settings.railway_public_domain.strip():
    cors_origins.add(f"https://{settings.railway_public_domain.strip()}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str | int]:
    db_status = "unknown"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "app_env": settings.app_env,
        "app_port": settings.app_port,
        "database": db_status,
    }


static_path = resolve_static_dir(settings.static_dir)
if static_path is not None:
    mount_frontend(app, static_path)
