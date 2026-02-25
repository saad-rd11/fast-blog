from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db

# ---------------------------------------------------------------------------
# Configuration (loaded from environment in main.py via dotenv)
# ---------------------------------------------------------------------------
import os

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


# ---------------------------------------------------------------------------
# Password hashing (using bcrypt directly — passlib is unmaintained)
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# ---------------------------------------------------------------------------
# JWT token helpers
# ---------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Return the payload dict or None if the token is invalid/expired."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Dependency: optional current user (returns None if not authenticated)
# ---------------------------------------------------------------------------
async def get_current_user_optional(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    sub: str | None = payload.get("sub")
    if sub is None:
        return None

    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        return None

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalars().first()


# ---------------------------------------------------------------------------
# Dependency: require authenticated user (raises 401 otherwise)
# ---------------------------------------------------------------------------
async def require_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.User:
    user = await get_current_user_optional(request, db)
    if user is None:
        # For API requests return JSON 401; for HTML redirect to login
        if request.url.path.startswith("/api"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        from fastapi.responses import RedirectResponse

        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Not authenticated",
            headers={"Location": "/login"},
        )
    return user


# ---------------------------------------------------------------------------
# Dependency: require admin user
# ---------------------------------------------------------------------------
async def require_admin(
    current_user: Annotated[models.User, Depends(require_current_user)],
) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
