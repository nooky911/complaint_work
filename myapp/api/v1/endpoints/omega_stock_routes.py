"""Маршруты для просмотра складских документов Omega"""

import logging
from datetime import date
from typing import Annotated, Awaitable, Literal, TypeVar

import oracledb
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response

from myapp.auth.dependencies import require_viewer_or_higher
from myapp.models.user import User
from myapp.schemas.omega_stock import (
    OmegaInplantInvoice,
    OmegaOutboundInvoice,
    OmegaReceipt,
    OmegaStockFile,
    OmegaStockItem,
    OmegaStockWarehouse,
)
from myapp.services.omega_stock_service import OmegaStockService

router = APIRouter(prefix="/omega-stock", tags=["Склад Omega"])
logger = logging.getLogger(__name__)
service = OmegaStockService()
StockKind = Literal["receipts", "inplant", "outbound"]
T = TypeVar("T")


async def _read(operation: Awaitable[T]) -> T:
    try:
        return await operation
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except oracledb.Error as exc:
        logger.exception("Не удалось прочитать складские документы Omega")
        raise HTTPException(
            status_code=503, detail="Omega сейчас недоступна"
        ) from exc


@router.get(
    "/warehouses/{kind}",
    response_model=list[OmegaStockWarehouse],
    summary="Получить склады для выбранного вида документов",
)
async def get_warehouses(
    kind: StockKind,
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await _read(service.list_warehouses(kind))


@router.get(
    "/documents/{kind}",
    response_model=list[OmegaReceipt | OmegaInplantInvoice | OmegaOutboundInvoice],
    summary="Найти складские документы",
)
async def get_documents(
    kind: StockKind,
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    response: Response,
    warehouse_ids: Annotated[list[int] | None, Query()] = None,
    number: Annotated[str | None, Query(max_length=100)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    response.headers["Cache-Control"] = "no-store"
    return await _read(
        service.list_documents(
            kind, warehouse_ids, number, date_from, date_to, offset, limit
        )
    )


@router.get(
    "/documents/{kind}/{document_id}/items",
    response_model=list[OmegaStockItem],
    summary="Получить состав складского документа",
)
async def get_document_items(
    kind: StockKind,
    document_id: Annotated[int, Path(ge=1)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    items = await _read(service.list_items(kind, document_id))
    if items is None:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return items


@router.get(
    "/documents/{kind}/{document_id}/files",
    response_model=list[OmegaStockFile],
    summary="Получить вложения складского документа",
)
async def get_document_files(
    kind: StockKind,
    document_id: Annotated[int, Path(ge=1)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    files = await _read(service.list_files(kind, document_id))
    if files is None:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return files


@router.get(
    "/documents/{kind}/{document_id}/files/{file_id}",
    summary="Открыть вложение складского документа",
)
async def get_document_file(
    kind: StockKind,
    document_id: Annotated[int, Path(ge=1)],
    file_id: Annotated[int, Path(ge=1)],
    _user: Annotated[User, Depends(require_viewer_or_higher)],
):
    file = await _read(service.get_file(kind, document_id, file_id))
    if file is None:
        raise HTTPException(status_code=404, detail="Вложение не найдено")
    content = file
    media_type = "application/pdf" if content.startswith(b"%PDF") else "application/octet-stream"
    extension = ".pdf" if media_type == "application/pdf" else ""
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="omega-{file_id}{extension}"',
            "Cache-Control": "no-store",
        },
    )
