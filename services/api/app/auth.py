from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, Depends, HTTPException, status
from investwatch_common.config import settings
from investwatch_common.db import get_db
from investwatch_common.models import User
from jose import JWTError, jwt
from sqlalchemy.orm import Session

hasher = PasswordHasher()

COOKIE_NAME = "iw_session"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def create_access_token(user: User) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user.id), "role": user.role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    iw_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    if not iw_session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = jwt.decode(iw_session, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session") from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return user
