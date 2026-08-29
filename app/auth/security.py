import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from pwdlib import PasswordHash
from app.config import settings



SECRET_KEY = settings.SECRET_KEY

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    password_hash_value: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        password_hash_value,
    )


def create_access_token(
    user_id: str,
) -> str:

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> str | None:

    print("\n---------- JWT DIAGNOSTIC ----------")
    print("Token received:", bool(token))
    print("Token length:", len(token) if token else 0)

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        print("JWT payload:", payload)

        user_id = payload.get("sub")

        print("JWT sub:", repr(user_id))
        print("------------------------------------\n")

        if not user_id:
            return None

        return user_id

    except JWTError as e:
        print("JWT ERROR:", type(e).__name__, str(e))
        print("------------------------------------\n")
        return None