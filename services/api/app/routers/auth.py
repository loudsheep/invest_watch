from fastapi import APIRouter, Depends, HTTPException, Response, status
from investwatch_common.db import get_db
from investwatch_common.models import User
from investwatch_common.schemas import LoginRequest, UserOut
from sqlalchemy.orm import Session

from ..auth import COOKIE_NAME, create_access_token, get_current_user, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token = create_access_token(user)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 8,
    )
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
