from fastapi import APIRouter, Depends, HTTPException, status, Form
from myapp.auth.security import verify_password
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.auth.tokens import create_access_token
from myapp.config import settings
from myapp.database.base import get_db
from myapp.schemas.users import TokenResponse
from myapp.services.user_service import UserService


router = APIRouter(
    prefix="/auth",
    tags=["Аутентификация "],
)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Вход в систему",
)
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Аутентифицирует пользователя и возвращает JWT токен доступа"""
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    # Используем username как login
    user = await UserService.get_by_login(session, username)

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
    return TokenResponse(
        access_token=access_token, token_type="bearer", expires_in=expires_in
    )
