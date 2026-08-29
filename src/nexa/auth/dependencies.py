from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from nexa.auth.permissions import Permission, Role, has_permission
from nexa.auth.security import decode_token
from nexa.db.connection import engine
from nexa.db.models import User

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class UserContext:
    user_id: str
    role: Role
    full_name: str


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> UserContext:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")

    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")

    with Session(engine) as session:
        user = session.get(User, payload["sub"])
        if user is None or not user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")

        return UserContext(
            user_id=user.id,
            role=Role(user.role),
            full_name=user.full_name,
        )


def require(permission: Permission):
    def guard(user: UserContext = Depends(current_user)) -> UserContext:
        if not has_permission(user.role, permission):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"missing permission: {permission.value}",
            )
        return user

    return guard