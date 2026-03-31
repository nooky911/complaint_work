from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.database.base import get_db
from myapp.models.user import User
from myapp.auth.dependencies import require_viewer_or_higher
from myapp.schemas import CaseFilterParams
from myapp.services.export_service import ExportService
from myapp.utils.file_helpers import handle_file_not_found

router = APIRouter(tags=["Экспорт данных"])


@router.get("/export", summary="Скачать список случаев в формате Excel")
async def export_cases_to_excel(
    params: Annotated[CaseFilterParams, Query()],
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer_or_higher),
):
    """Генерация и скачивание Excel-файла с учетом примененных фильтров"""
    try:
        file_stream, encoded_filename = await ExportService.get_cases_export_stream(
            session, params
        )

        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"
            },
        )
    except Exception as e:
        if str(e) == "Нет данных для экспорта":
            raise HTTPException(status_code=404, detail=str(e))
        handle_file_not_found(e)
