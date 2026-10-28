from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Annotated

from myapp.auth.dependencies import get_current_user, require_superadmin
from myapp.database.base import get_db
from myapp.models.user import User
from myapp.schemas.users import UserResponse, UserPasswordChange, AdminUserData
from myapp.services.user_service import UserService
from myapp.services.user_access_service import UserAccessService
from myapp.services.admin_user_service import AdminUserService

router = APIRouter(prefix="/users", tags=["Пользователь"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить профиль",
)
async def get_me(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Получает профиль текущего авторизованного пользователя"""
    user_data = UserResponse.model_validate(current_user)
    user_data.partner_ids = list(
        (await session.scalars(UserAccessService.partner_ids(current_user.id))).all()
    )
    return user_data


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


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Список всех активных пользователей",
)
async def get_users_list(
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Возвращает список всех доступных пользователей"""
    return await UserService.get_all_active_users(session)


@router.get(
    "/admin",
    response_model=list[UserResponse],
    summary="Все пользователи для админ-панели",
)
async def admin_users(
    session: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_superadmin)],
):
    """Возвращает пользователей для админ-панели"""
    return await AdminUserService.list_users(session)


async def admin_action(action):
    """Преобразует ошибки административного действия в ответ API"""
    try:
        return await action
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except LookupError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except IntegrityError:
        raise HTTPException(
            409,
            "Данные пользователя конфликтуют с существующей записью. Обновите список и повторите действие.",
        )


@router.post("/admin", status_code=201, summary="Создать пользователя")
async def admin_create_user(
    data: AdminUserData,
    session: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_superadmin)],
):
    """Создаёт пользователя через админ-панель"""
    return await admin_action(AdminUserService.create_user(session, admin.id, data))


@router.put("/admin/{user_id}", summary="Изменить пользователя и взаимный доступ")
async def admin_update_user(
    user_id: int,
    data: AdminUserData,
    session: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_superadmin)],
):
    """Обновляет пользователя через админ-панель"""
    return await admin_action(
        AdminUserService.update_user(session, admin.id, user_id, data)
    )


@router.post("/admin/{user_id}/reset-password", summary="Сбросить пароль пользователя")
async def admin_reset_password(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_superadmin)],
):
    """Сбрасывает пароль через админ-панель"""
    return await admin_action(
        AdminUserService.reset_password(session, admin.id, user_id)
    )
