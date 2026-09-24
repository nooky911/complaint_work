from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.auth.dependencies import require_viewer_or_higher
from myapp.database.base import get_db
from myapp.models.user import User
from myapp.schemas.product_passports import (
    ProductPassportModelResponse,
    ProductPassportResponse,
    ProductPassportSearchItem,
)
from myapp.services.product_passport_service import ProductPassportService

router = APIRouter(prefix="/product-passports", tags=["Паспорта изделий"])


@router.get(
    "/models",
    response_model=list[ProductPassportModelResponse],
    summary="Получить модели с паспортами",
)
async def get_product_passport_models(
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Возвращает только модели, для которых уже импортированы паспорта"""
    return await ProductPassportService.get_models(session)


@router.get(
    "/search",
    response_model=list[ProductPassportSearchItem],
    summary="Найти паспорт локомотива",
)
async def search_product_passports(
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    locomotive_model_id: Annotated[int, Query(ge=1)],
    product_number: Annotated[str, Query(min_length=1, max_length=50)],
):
    """Ищет до двадцати паспортов по модели и началу номера"""
    return await ProductPassportService.search(
        session=session,
        locomotive_model_id=locomotive_model_id,
        product_number=product_number,
    )


@router.get(
    "/{passport_id}",
    response_model=ProductPassportResponse,
    summary="Получить импортированный паспорт",
)
async def get_product_passport(
    passport_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Возвращает паспорт и все узлы его дерева из БД"""
    passport = await ProductPassportService.get_by_id(session, passport_id)
    if passport is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Паспорт не найден"
        )
    return ProductPassportService.to_response(passport)
