from fastapi import APIRouter, Depends, Path, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.schemas.cases import CaseList, CaseDetail, CaseCreate, CaseUpdate
from myapp.schemas.filters import CaseFilterParams
from myapp.services.case_service import CaseService
from myapp.services.case_filter_service import CaseFilterService
from myapp.database.base import get_db
from .warranty_routes import router as warranty_router


router = APIRouter(prefix="/cases", tags=["Случаи неисправности"] )

router.include_router(warranty_router)


# Полный список и фильтрация
@router.get(
    "/", response_model=list[CaseList],
    summary="Получить список случаев ремонта с (возможной) фильтрацией",
    status_code=status.HTTP_200_OK
)
async def list_and_filter_cases(params: CaseFilterParams = Depends(), session: AsyncSession = Depends(get_db)):
    return await CaseFilterService.filter_cases(session, params)


# Создание
@router.post("/", response_model=CaseDetail, status_code=status.HTTP_201_CREATED, summary="Создание случая")
async def create_case(case_data: CaseCreate, session: AsyncSession = Depends(get_db)):
    return await CaseService.create_case(session, case_data)


# Детали случаи
@router.get("/{case_id}", response_model=CaseDetail, summary="Получить детальную информацию о случае")
async def get_case_detail(
        case_id: int = Path(..., description="ID случая неисправности", ge=1),
        session: AsyncSession = Depends(get_db)
):
    case = await CaseService.get_case(session, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Случай с ID {case_id} не найден")
    return case


# Редактирование
@router.patch("/{case_id}", response_model=CaseDetail, summary="Редактирование случая")
async def update_case(
        case_data: CaseUpdate,
        case_id: int = Path(..., description="ID случая неисправности", ge=1),
        session: AsyncSession = Depends(get_db)
):
    updated_case = await CaseService.update_case(session, case_id, case_data)
    if not updated_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Случай с ID {case_id} для обновления не найден"
        )
    return updated_case


#Удаление случая
@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить случай по ID")
async def delete_case(
        case_id: int = Path(..., description="ID случая неисправности", ge=1),
        session: AsyncSession = Depends(get_db)
):
    deleted_count = await CaseService.delete_case(session, case_id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Случай с ID {case_id} не найден."
        )

    return None