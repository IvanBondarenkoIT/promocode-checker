import pytest
from app.core.admin_auth import AdminAuthError, create_admin_token, verify_admin_token
from app.models.enums import AdminRole


def test_admin_token_roundtrip() -> None:
    token = create_admin_token(
        username="admin",
        role=AdminRole.ADMIN,
        secret_key="secret",
        ttl_seconds=3600,
    )
    identity = verify_admin_token(token, secret_key="secret")
    assert identity.username == "admin"
    assert identity.role == AdminRole.ADMIN


def test_admin_token_rejects_bad_signature() -> None:
    token = create_admin_token(
        username="admin",
        role=AdminRole.ADMIN,
        secret_key="secret",
    )
    with pytest.raises(AdminAuthError):
        verify_admin_token(token + "x", secret_key="secret")
