from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.auth.dependencies import require_can_edit_case, require_viewer_or_higher
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.user import User
from myapp.schemas.warranty import WarrantyWorkUpdate, WarrantyWorkResponse
from myapp.services import CaseValidationError
from myapp.services.warranty_service import WarrantyService
from myapp.database.base import get_db


router = APIRouter(tags=["Рекламационная работа"])


# Данные случая по рекламационная работа
@router.get("/", response_model=WarrantyWorkResponse, summary="Вкладка рекл. работы")
async def get_warranty_work_data(
    case_id: Annotated[int, Path(description="ID случая", ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Выводит данные вкладки рекламационной работе"""
    warranty_work = await WarrantyService.get_warranty_by_case(session, case_id)

    if not warranty_work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рекл. работа для случая ID {case_id} не найдена.",
        )

    return warranty_work


# Редактирование случая
@router.patch(
    "/",
    response_model=WarrantyWorkResponse,
    summary="Редактирование данных по рекл. работе",
)
async def update_warranty_work_data(
    warranty_data: WarrantyWorkUpdate,
    expected_revision: Annotated[int, Query(ge=1)],
    case_id: Annotated[int, Path(description="ID случая", ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _user_and_case: Annotated[
        tuple[User, RepairCaseEquipment], Depends(require_can_edit_case)
    ],
):
    """Позволяет редактировать поля рекламационной работы"""
    try:
        updated_warranty = await WarrantyService.update_warranty_work(
            session, case_id, warranty_data, expected_revision=expected_revision
        )
    except CaseValidationError as exc:
        raise HTTPException(409 if exc.field == "revision" else 422, str(exc)) from exc

    if not updated_warranty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Случай рекл. работы ID {case_id} не найден для обновления.",
        )

    return updated_warranty
