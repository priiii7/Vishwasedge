"""Auth, DB, Redis dependency injection for FastAPI routes."""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import get_settings
from backend.core.security import decode_access_token, has_permission, permissions_for_role

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    username: str
    role: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> CurrentUser:
    settings = get_settings()

    if api_key and api_key == settings.default_api_key:
        return CurrentUser(username="api-key-client", role="operator")

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return CurrentUser(username=payload["sub"], role=payload.get("role", "viewer"))


def require_permission(permission: str):
    async def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not has_permission(user.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires '{permission}' permission")
        return user

    return _checker


def user_permissions(user: CurrentUser) -> list[str]:
    return permissions_for_role(user.role)
