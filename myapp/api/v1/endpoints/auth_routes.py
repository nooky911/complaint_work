from fastapi import APIRouter, Depends, HTTPException, status, Form, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.auth.tokens import create_access_token
from myapp.auth.security import verify_password
from myapp.config import settings
from myapp.database.base import get_db
from myapp.schemas.users import UserResponse
from myapp.services.user_service import UserService


router = APIRouter(
    prefix="/auth",
    tags=["Аутентификация "],
)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Вход в систему",
)
async def login_user(
    response: Response,
    login: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Аутентифицирует пользователя и возвращает JWT токен доступа"""

    user = await UserService.get_by_login(session, login)

    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    # Установка cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,  # !!! ПОМЕНЯТЬ!!!
        samesite="lax",
        path="/",
    )

    return UserResponse(
        id=user.id,
        login=user.login,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/logout", status_code=status.HTTP_200_OK, summary="Выход из системы")
async def logout(response: Response):
    """Удаляет cookie с токеном"""
    response.delete_cookie(key="access_token", path="/")
