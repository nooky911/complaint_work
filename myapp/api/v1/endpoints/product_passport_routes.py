import logging
from datetime import date
from typing import Annotated
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.auth.dependencies import (
    require_editor_or_superadmin,
    require_superadmin,
    require_viewer_or_higher,
)
from myapp.database.base import get_db
from myapp.models.user import User
from myapp.schemas.product_passports import (
    PassportCorrection,
    PassportReplacementPreview,
    ProductPassportModelResponse,
    ProductPassportResponse,
    ProductPassportSearchItem,
)
from myapp.services import CaseValidationError
from myapp.services.omega_services.passport_history_service import (
    PassportHistoryService,
)
from myapp.services.omega_services.passport_position_service import (
    PassportPositionService,
)
from myapp.services.omega_services.product_passport_export_service import (
    ProductPassportExportService,
)
from myapp.services.omega_services.product_passport_service import (
    ProductPassportService,
)


router = APIRouter(prefix="/product-passports", tags=["Паспорта изделий"])
logger = logging.getLogger(__name__)


@router.get(
    "/models",
    response_model=list[ProductPassportModelResponse],
    summary="Получить модели с паспортами",
)
async def get_product_passport_models(
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Возвращает модели с паспортами введённых в эксплуатацию локомотивов"""
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
    """Ищет до двадцати доступных паспортов по модели и началу номера"""
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
    """Возвращает доступный паспорт и все узлы его дерева из БД"""
    passport = await ProductPassportService.get_by_id(session, passport_id)
    if passport is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Паспорт не найден"
        )
    return ProductPassportService.to_response(passport)


@router.get("/{passport_id}/export", summary="Скачать паспорт в Excel")
async def export_product_passport(
    passport_id: Annotated[int, Path(ge=1)],
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Выгружает полное дерево и характеристики на одном листе XLSX"""
    try:
        result = await ProductPassportExportService.export(session, passport_id)
    except Exception:
        logger.exception("Не удалось выгрузить паспорт %s в Excel", passport_id)
        raise HTTPException(
            status_code=500, detail="Не удалось создать файл паспорта"
        ) from None
    if result is None:
        raise HTTPException(status_code=404, detail="Паспорт не найден")
    stream, filename = result
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{quote(filename)}"
        },
    )


@router.get("/{passport_id}/equipment-options")
async def passport_equipment_options(
    passport_id: int,
    component_equipment_id: int,
    section_mask: int,
    fault_date: date,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    element_equipment_id: int | None = None,
    case_id: int | None = None,
    component_node_ids: Annotated[
        str | None, Query(pattern=r"^[0-9]+(,[0-9]+)*$")
    ] = None,
):
    """Возвращает паспортные экземпляры для выбора в случае"""
    try:
        return await PassportPositionService.options(
            session,
            passport_id,
            component_equipment_id,
            element_equipment_id,
            section_mask,
            fault_date,
            case_id,
            (
                [int(n) for n in component_node_ids.split(",")]
                if component_node_ids
                else None
            ),
        )
    except CaseValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/{passport_id}/replacement-preview")
async def passport_replacement_preview(
    passport_id: int,
    data: PassportReplacementPreview,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_editor_or_superadmin)],
):
    """Возвращает состав установленного оборудования для заполнения"""
    try:
        return await PassportPositionService.preview(
            session, passport_id, data.model_dump()
        )
    except CaseValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/{passport_id}/nodes/{node_id}/history")
async def passport_position_history(
    passport_id: int,
    node_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Возвращает историю выбранной позиции паспорта"""
    try:
        return await PassportHistoryService.history(session, passport_id, node_id)
    except CaseValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/{passport_id}/nodes/{node_id}/types")
async def passport_position_types(
    passport_id: int,
    node_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_superadmin)],
):
    """Возвращает допустимые типы для ручного исправления позиции"""
    _, nodes, states, equipment, _ = await PassportPositionService.load(
        session, passport_id
    )
    if node_id not in nodes:
        raise HTTPException(404, "Позиция не найдена")
    return PassportPositionService.allowed_types(
        states[node_id].get("equipment_id"), equipment
    )


@router.patch("/{passport_id}/nodes/{node_id}")
async def correct_passport_position(
    passport_id: int,
    node_id: int,
    data: PassportCorrection,
    session: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_superadmin)],
):
    """Исправляет данные позиции паспорта с сохранением истории"""
    try:
        await PassportHistoryService.correct(
            session, passport_id, node_id, data.model_dump(exclude_unset=True), actor
        )
    except CaseValidationError as exc:
        raise HTTPException(409 if exc.field == "revision" else 422, str(exc)) from exc
    return {"status": "ok"}
