from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from auth import (
    create_access_token,
    get_current_user_optional,
    hash_password,
    verify_password,
)
from database import get_db
from schemas import LoginSchema, TokenResponse, UserCreate, UserResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------------------
# HTML page routes
# ---------------------------------------------------------------------------


@router.get("/login", include_in_schema=False, name="login")
async def login_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    current_user = await get_current_user_optional(request, db)
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request, "login.html", {"title": "Login", "current_user": None}
    )


@router.get("/register", include_in_schema=False, name="register")
async def register_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    current_user = await get_current_user_optional(request, db)
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request, "register.html", {"title": "Register", "current_user": None}
    )


@router.get("/logout", include_in_schema=False, name="logout")
async def logout_page():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------


@router.post(
    "/api/auth/login",
    response_model=TokenResponse,
    tags=["auth"],
)
async def api_login(
    credentials: LoginSchema,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(models.User.username == credentials.username)
    )
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(data={"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 30,  # 30 minutes
    )
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/api/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
async def api_register(
    user_data: UserCreate,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Check username uniqueness
    result = await db.execute(
        select(models.User).where(models.User.username == user_data.username)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check email uniqueness
    result = await db.execute(
        select(models.User).where(models.User.email == user_data.email)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token(data={"sub": str(new_user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 30,
    )
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(new_user),
    )


@router.post("/api/auth/logout", tags=["auth"])
async def api_logout(response: Response):
    response.delete_cookie("access_token")
    return {"detail": "Logged out successfully"}
