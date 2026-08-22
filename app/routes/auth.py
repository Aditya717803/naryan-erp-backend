from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)

from app.auth.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(
            User.user_id == login_data.user_id.strip()
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    if not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID or password",
        )

    access_token = create_access_token(
        user.user_id,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    print("\n========== AUTH DIAGNOSTIC ==========")
    print("Token received:", bool(token))
    print("Token length:", len(token) if token else 0)

    if token:
        print("Token prefix:", token[:20])

    try:
        user_id = decode_access_token(token)
        print("Decoded user_id:", repr(user_id))
    except Exception as e:
        print("JWT decode exception:", type(e).__name__, str(e))
        user_id = None

    if user_id is None:
        print("RESULT: JWT INVALID")
        print("====================================\n")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    user = db.scalar(
        select(User).where(
            User.user_id == user_id
        )
    )

    print("Database user found:", user is not None)

    if user:
        print("Database user_id:", repr(user.user_id))
        print("Database active:", user.is_active)

    if user is None:
        print("RESULT: USER NOT FOUND")
        print("====================================\n")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.is_active:
        print("RESULT: USER INACTIVE")
        print("====================================\n")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    print("RESULT: AUTHENTICATION SUCCESS")
    print("====================================\n")

    return user

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.post(
    "/token",
    response_model=TokenResponse,
)
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(
            User.user_id == form_data.username.strip()
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    if not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID or password",
        )

    access_token = create_access_token(
        user.user_id,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }