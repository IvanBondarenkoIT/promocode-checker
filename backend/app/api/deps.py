from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.admin_auth import AdminAuthError, AdminIdentity, verify_admin_token
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.enums import AdminRole

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_current_admin(
    settings: AppSettings,
    authorization: Annotated[str | None, Header()] = None,
) -> AdminIdentity:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        return verify_admin_token(token, secret_key=settings.app_secret_key)
    except AdminAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_admin(actor: Annotated[AdminIdentity, Depends(get_current_admin)]) -> AdminIdentity:
    if actor.role != AdminRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return actor


CurrentAdmin = Annotated[AdminIdentity, Depends(get_current_admin)]
AdminOnly = Annotated[AdminIdentity, Depends(require_admin)]
