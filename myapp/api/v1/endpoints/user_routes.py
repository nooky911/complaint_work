from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.auth.dependencies import get_current_user
from myapp.database.base import get_db
from myapp.models.user import User
from myapp.schemas.users import UserResponse, UserPasswordChange
from myapp.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Пользователь"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить профиль",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Получает профиль текущего авторизованного пользователя"""
    return UserResponse.model_validate(current_user)


@router.post(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Смена пароля",
    response_description="Успешное изменение пароля",
)
async def change_user_password(
    password_data: UserPasswordChange,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Смена пароля текущего пользователя"""
    try:
        await UserService.change_password(session, current_user, password_data)

        return {"detail": "Пароль успешно изменен"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
