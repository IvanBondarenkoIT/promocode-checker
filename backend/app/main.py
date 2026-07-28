from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal

settings = get_settings()

app = FastAPI(
    title="Promocode Checker",
    version="0.1.0",
    summary="Backend API for promo validation, cashier flows, admin tools, and ERP reconciliation.",
)


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
