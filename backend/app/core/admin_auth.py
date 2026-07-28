"""Signed admin session tokens (stdlib only)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from app.models.enums import AdminRole


class AdminAuthError(Exception):
    pass


@dataclass(frozen=True)
class AdminIdentity:
    username: str
    role: AdminRole


def _encode_payload(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_payload(data: str) -> dict:
    raw = base64.urlsafe_b64decode(data.encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def create_admin_token(
    *,
    username: str,
    role: AdminRole,
    secret_key: str,
    ttl_seconds: int = 86_400,
) -> str:
    payload = {
        "sub": username,
        "role": role.value,
        "exp": int(time.time()) + ttl_seconds,
    }
    data = _encode_payload(payload)
    signature = hmac.new(
        secret_key.encode("utf-8"),
        data.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{data}.{signature}"


def verify_admin_token(token: str, *, secret_key: str) -> AdminIdentity:
    try:
        data, signature = token.rsplit(".", 1)
    except ValueError as exc:
        raise AdminAuthError("Invalid token format") from exc

    expected = hmac.new(
        secret_key.encode("utf-8"),
        data.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise AdminAuthError("Invalid token signature")

    payload = _decode_payload(data)
    if int(payload.get("exp", 0)) < int(time.time()):
        raise AdminAuthError("Token expired")

    username = str(payload.get("sub", "")).strip()
    role_raw = str(payload.get("role", "")).strip()
    if not username or role_raw not in {AdminRole.ADMIN.value, AdminRole.VIEWER.value}:
        raise AdminAuthError("Invalid token payload")

    return AdminIdentity(username=username, role=AdminRole(role_raw))
