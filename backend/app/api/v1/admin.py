import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AdminOnly, AppSettings, CurrentAdmin, DbSession
from app.core.admin_auth import create_admin_token
from app.models import CampaignKind
from app.schemas.admin import (
    ActiveScopeResponse,
    ActiveScopeUpdateRequest,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminMeResponse,
    AdminMutationResponse,
    AdminTableName,
    DashboardResponse,
    FraudWarningPatchRequest,
    PromocodePatchRequest,
    TableListResponse,
)
from app.services.admin_auth import authenticate_admin
from app.services.admin_dashboard import get_dashboard
from app.services.admin_mutations import AdminMutationError, patch_fraud_warning, patch_promocode
from app.services.admin_scope import ScopeUpdateError, get_active_scope, update_active_scope
from app.services.admin_tables import list_table_rows

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(payload: AdminLoginRequest, settings: AppSettings) -> AdminLoginResponse:
    identity = authenticate_admin(payload.username, payload.password, settings)
    if identity is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_admin_token(
        username=identity.username,
        role=identity.role,
        secret_key=settings.app_secret_key,
    )
    return AdminLoginResponse(
        token=token,
        username=identity.username,
        role=identity.role.value,
    )


@router.get("/me", response_model=AdminMeResponse)
def admin_me(actor: CurrentAdmin) -> AdminMeResponse:
    return AdminMeResponse(username=actor.username, role=actor.role.value)


@router.get("/dashboard", response_model=DashboardResponse)
def admin_dashboard(db: DbSession, actor: CurrentAdmin) -> DashboardResponse:
    _ = actor
    return get_dashboard(db)


@router.get("/scope", response_model=ActiveScopeResponse)
def admin_get_scope(db: DbSession, actor: CurrentAdmin) -> ActiveScopeResponse:
    _ = actor
    return get_active_scope(db)


@router.put("/scope", response_model=ActiveScopeResponse)
def admin_set_scope(
    payload: ActiveScopeUpdateRequest,
    db: DbSession,
    actor: AdminOnly,
) -> ActiveScopeResponse:
    try:
        return update_active_scope(
            db,
            actor=actor,
            requested_kind=payload.active_campaign_kind,
            reason=payload.reason,
        )
    except ScopeUpdateError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/tables/{table_name}", response_model=TableListResponse)
def admin_table(
    table_name: AdminTableName,
    db: DbSession,
    actor: CurrentAdmin,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    campaign_code: Annotated[str | None, Query(max_length=64)] = None,
    kind: Annotated[CampaignKind | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status", max_length=32)] = None,
    search: Annotated[str | None, Query(max_length=64)] = None,
) -> TableListResponse:
    _ = actor
    return list_table_rows(
        db,
        table=table_name,
        limit=limit,
        offset=offset,
        campaign_code=campaign_code,
        kind=kind,
        status=status_filter,
        search=search,
    )


@router.patch("/promocodes/{promocode_id}", response_model=AdminMutationResponse)
def admin_patch_promocode(
    promocode_id: uuid.UUID,
    payload: PromocodePatchRequest,
    db: DbSession,
    actor: AdminOnly,
) -> AdminMutationResponse:
    try:
        return patch_promocode(db, actor=actor, promocode_id=promocode_id, payload=payload)
    except AdminMutationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.patch("/fraud-warnings/{warning_id}", response_model=AdminMutationResponse)
def admin_patch_fraud_warning(
    warning_id: int,
    payload: FraudWarningPatchRequest,
    db: DbSession,
    actor: AdminOnly,
) -> AdminMutationResponse:
    try:
        return patch_fraud_warning(db, actor=actor, warning_id=warning_id, payload=payload)
    except AdminMutationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
