from fastapi import APIRouter, Depends, Path, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.user import User
from myapp.schemas.cases import CaseList, CaseDetail, CaseCreate, CaseUpdate
from myapp.schemas.filters import CaseFilterParams
from myapp.services.case_service import CaseService
from myapp.services.case_filter_service import CaseFilterService
from myapp.database.base import get_db
from .warranty_routes import router as warranty_router
from myapp.auth.dependencies import (
    require_editor_or_superadmin,
    require_viewer_or_higher,
    require_can_edit_case,
)

router = APIRouter(prefix="/cases", tags=["Случаи неисправности"])

router.include_router(warranty_router, prefix="/{case_id}/warranty")


# Полный список и фильтрация
@router.get(
    "/",
    response_model=list[CaseList],
    summary="Получить список случаев ремонта с (возможной) фильтрацией",
    status_code=status.HTTP_200_OK,
)
async def list_and_filter_cases(
    params: Annotated[CaseFilterParams, Query()],
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Получить список случаев неисправности, используя параметры фильтрации"""
    return await CaseFilterService.filter_cases(session, params)


# Создание
@router.post(
    "/",
    response_model=CaseDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Создание случая",
)
async def create_case(
    case_data: CaseCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_editor_or_superadmin)],
):
    """Создает новый случай неисправности от имени текущего пользователя"""
    target_user_id = current_user.id

    if current_user.role == "superadmin" and case_data.user_id is not None:
        target_user_id = case_data.user_id

    return await CaseService.create_case(session, case_data, target_user_id)


# Детали случаи
@router.get(
    "/{case_id}",
    response_model=CaseDetail,
    summary="Получить детальную информацию о случае",
)
async def get_case_detail(
    case_id: Annotated[int, Path(description="ID случая неисправности", ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Получает полную информацию о случае по его ID, включая все связанные данные"""
    case = await CaseService.get_case(session, case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Случай с ID {case_id} не найден.",
        )

    return case


# Редактирование
@router.patch("/{case_id}", response_model=CaseDetail, summary="Редактирование случая")
async def update_case(
    case_data: CaseUpdate,
    case_id: Annotated[int, Path(description="ID случая неисправности", ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_and_case: Annotated[
        tuple[User, RepairCaseEquipment], Depends(require_can_edit_case)
    ],
):
    """Обновляет основные поля случая и связанные данные WarrantyWork"""
    current_user, _case = user_and_case
    
    # Проверка прав на смену владельца случая
    if case_data.user_id is not None and current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только superadmin может менять владельца случая",
        )
    
    updated_case = await CaseService.update_case(session, case_id, case_data)

    if not updated_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Случай с ID {case_id} для обновления не найден.",
        )

    return updated_case


# Удаление случая
@router.delete(
    "/{case_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить случай по ID"
)
async def delete_case(
    case_id: Annotated[int, Path(description="ID случая неисправности", ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _user_and_case: Annotated[
        tuple[User, RepairCaseEquipment], Depends(require_can_edit_case)
    ],
):
    """Удаляет случай по его ID. Также удаляет связанные записи WarrantyWork"""
    deleted_count = await CaseService.delete_case(session, case_id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Случай с ID {case_id} не найден.",
        )

    return None
