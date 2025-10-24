from fastapi import APIRouter, Depends, Path, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.warranty import WarrantyWorkUpdate, WarrantyWorkResponse
from services.warranty_service import WarrantyService
from database.base import get_db

router = APIRouter(prefix="/cases/{case_id}/warranty", tags=["Рекламационная работа"])


# Данные случая по рекламационная работа
@router.get("/", response_model=WarrantyWorkResponse, summary="Вкладка рекл. работы")
async def get_warranty_work(
        case_id: int = Path(..., description="ID случая неисправности", ge=1),
        session: AsyncSession = Depends(get_db)
):
    warranty_work = await WarrantyService.get_warranty_by_case(session, case_id)

    if not warranty_work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рекл. работа для случая ID {case_id} не найдена"
        )

    return warranty_work


# Редактирование случая
@router.patch("/", response_model=WarrantyWorkResponse, summary="Редактирование данных по рекл. работе")
async def update_warranty_work(
        warranty_data: WarrantyWorkUpdate,
        case_id: int = Path(..., description="ID случая неисправности", ge=1),
        session: AsyncSession = Depends(get_db)
):
    updated_warranty = await WarrantyService.update_warranty_work(session, case_id, warranty_data)

    if not updated_warranty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Случай рекл. работы ID {case_id} не найден для обновления."
        )

    return updated_warranty