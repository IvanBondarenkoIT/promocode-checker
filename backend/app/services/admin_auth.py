from app.core.admin_auth import AdminIdentity
from app.core.config import Settings
from app.models.enums import AdminRole


def authenticate_admin(username: str, password: str, settings: Settings) -> AdminIdentity | None:
    user = username.strip()
    if user == settings.admin_username and password == settings.admin_password:
        return AdminIdentity(username=user, role=AdminRole.ADMIN)
    if user == settings.viewer_username and password == settings.viewer_password:
        return AdminIdentity(username=user, role=AdminRole.VIEWER)
    return None
