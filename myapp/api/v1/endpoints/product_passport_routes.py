import logging
from datetime import date
from typing import Annotated, Literal
from urllib.parse import quote
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
    File,
    Form,
    UploadFile,
    Response,
)
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.auth.dependencies import (
    require_editor_or_superadmin,
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
from myapp.services.omega_services.passport_file_service import PassportFileService
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


async def _passport_file_result(operation):
    """Преобразует ошибки работы со сканами в ответ API"""
    try:
        return await operation
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except CaseValidationError as exc:
        raise HTTPException(409 if exc.field == "revision" else 422, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(502, str(exc)) from exc


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
    section_mask: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    component_equipment_id: int | None = None,
    fault_date: date | None = None,
    element_equipment_id: int | None = None,
    case_id: int | None = None,
    component_node_ids: Annotated[
        str | None, Query(pattern=r"^[0-9]+(,[0-9]+)*$")
    ] = None,
):
    """Возвращает экземпляры на дату акта или текущий состав, пока дата не выбрана"""
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
    _user: Annotated[User, Depends(require_editor_or_superadmin)],
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
    actor: Annotated[User, Depends(require_editor_or_superadmin)],
):
    """Исправляет данные позиции паспорта с сохранением истории"""
    try:
        await PassportHistoryService.correct(
            session, passport_id, node_id, data.model_dump(exclude_unset=True), actor
        )
    except CaseValidationError as exc:
        raise HTTPException(409 if exc.field == "revision" else 422, str(exc)) from exc
    return {"status": "ok"}


@router.get("/{passport_id}/nodes/{node_id}/files")
async def passport_node_files(
    passport_id: int,
    node_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    event_id: Annotated[int | None, Query(ge=1)] = None,
    side: Literal["before", "after"] = "before",
):
    """Показывает файлы текущего или прежнего экземпляра оборудования"""
    return await _passport_file_result(
        PassportFileService.listing(session, passport_id, node_id, event_id, side)
    )


@router.get("/{passport_id}/nodes/{node_id}/file-history")
async def passport_node_file_history(
    passport_id: int,
    node_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Возвращает привязки файлов ко всем строкам истории выбранной позиции"""
    return await _passport_file_result(
        PassportFileService.history_files(session, passport_id, node_id)
    )


@router.post("/{passport_id}/nodes/{node_id}/files", status_code=201)
async def upload_passport_node_files(
    passport_id: int,
    node_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_editor_or_superadmin)],
    files: Annotated[list[UploadFile], File()],
    instance_key: Annotated[str, Form(min_length=1, max_length=80)],
    event_id: Annotated[int | None, Query(ge=1)] = None,
    side: Literal["before", "after"] = "before",
):
    """Прикрепляет сканы к экземпляру, показанному пользователю"""
    return await _passport_file_result(
        PassportFileService.upload(
            session, passport_id, node_id, files, actor, instance_key, event_id, side
        )
    )


@router.get("/{passport_id}/nodes/{node_id}/files/omega/{file_id}")
async def download_omega_passport_file(
    passport_id: int,
    node_id: int,
    file_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    instance_key: Annotated[str, Query(min_length=1, max_length=80)],
    event_id: Annotated[int | None, Query(ge=1)] = None,
    side: Literal["before", "after"] = "before",
):
    """Получает заводской файл из Omega при открытии ссылки"""
    content, filename = await _passport_file_result(
        PassportFileService.omega_content(
            session, passport_id, node_id, file_id, instance_key, event_id, side
        )
    )
    media_type = (
        "application/pdf"
        if content.startswith(b"%PDF-")
        else (
            "image/png"
            if content.startswith(b"\x89PNG\r\n\x1a\n")
            else (
                "image/jpeg"
                if content.startswith(b"\xff\xd8\xff")
                else "application/octet-stream"
            )
        )
    )
    disposition = "attachment" if media_type == "application/octet-stream" else "inline"
    return Response(
        content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"{disposition}; filename*=utf-8''{quote(filename, safe='')}",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{passport_id}/nodes/{node_id}/files/local/{file_id}")
async def download_local_passport_file(
    passport_id: int,
    node_id: int,
    file_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    """Открывает загруженный скан с проверкой принадлежности паспорту"""
    file, path = await _passport_file_result(
        PassportFileService.local_file(session, passport_id, node_id, file_id)
    )
    media_type = (
        file.mime_type
        if file.mime_type in ("application/pdf", "image/jpeg", "image/png")
        else "application/octet-stream"
    )
    return FileResponse(
        path,
        media_type=media_type,
        filename=file.original_name,
        content_disposition_type=(
            "inline" if media_type != "application/octet-stream" else "attachment"
        ),
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
