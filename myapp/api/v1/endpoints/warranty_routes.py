from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.schemas.warranty import WarrantyWorkUpdate, WarrantyWorkResponse
from myapp.services.warranty_service import WarrantyService
from myapp.database.base import get_db


router = APIRouter(tags=["Рекламационная работа"])


# Данные случая по рекламационная работа
@router.get("/", response_model=WarrantyWorkResponse, summary="Вкладка рекл. работы")
async def get_warranty_work_data(case_id: int, session: AsyncSession = Depends(get_db)):
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
    case_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Позволяет редактировать поля рекламационной работы"""
    updated_warranty = await WarrantyService.update_warranty_work(
        session, case_id, warranty_data
    )

    if not updated_warranty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Случай рекл. работы ID {case_id} не найден для обновления.",
        )

    return updated_warranty
