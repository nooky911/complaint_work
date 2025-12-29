from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, NoReturn

from myapp.auth.tokens import decode_token
from myapp.database.base import get_db
from myapp.models import RepairCaseEquipment
from myapp.models.user import User
from myapp.services.case_service import CaseService
from myapp.services.file_service import FileService


def raise_401(detail: str) -> NoReturn:
    """Быстрое создание 401 ошибки с WWW-Authenticate заголовком"""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Получает текущего авторизованного пользователя из cookie или заголовка"""

    # Получаем токен из кук или заголовка
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise_401("Not authenticated")

    # Декод токена
    payload = decode_token(token)
    if payload is None:
        raise_401("Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise_401("Invalid token format")

    # Преобразование user_id в int
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise_401("Invalid user ID format")

    # Получаем пользователя из БД
    user = await session.get(User, user_id_int)
    if user is None:
        raise_401("User not found")

    # Проверка на активность
    if not user.is_active:
        raise_401("User account is disabled")

    return user  # type: ignore[valid-type]


async def require_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Доступ только для superadmin"""
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required",
        )
    return current_user


async def require_can_edit_case(
    case_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> tuple[User, RepairCaseEquipment]:
    """
    Разрешает редактирование только:
    - superadmin для любого случая
    - создателю случая (по полю user_id)
    """
    case = await CaseService.get_case(session, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    # superadmin может всё
    if current_user.role == "superadmin":
        return current_user, case

    # только создатель кейса
    if getattr(case, "user_id", None) == current_user.id:
        return current_user, case

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can edit only cases you created",
    )


async def require_editor_or_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Доступ для editor и superadmin"""
    if current_user.role not in ("editor", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor or superadmin access required",
        )
    return current_user


async def require_viewer_or_higher(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Доступ для всех авторизованных пользователей (viewer, editor, superadmin)"""
    return current_user


async def require_can_edit_file_case(
    file_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> tuple[User, RepairCaseEquipment]:
    """
    Разрешает удаление файла только:
    - superadmin для любого файла
    - создателю случая, к которому привязан файл
    """
    # 1. Найти файл и case_id
    case_file = await FileService.get_file_by_id(session, file_id)

    if not case_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    case_id = case_file.case_id

    # 2. Получить Case для авторизации
    case = await CaseService.get_case(session, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated case not found",
        )

    # 3. Применить существующую логику авторизации
    if current_user.role == "superadmin":
        return current_user, case

    # только создатель кейса
    if getattr(case, "user_id", None) == current_user.id:
        return current_user, case

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can edit or delete files only in cases you created",
    )
