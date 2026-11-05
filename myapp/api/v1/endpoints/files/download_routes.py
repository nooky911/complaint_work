from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.models.case_files import FileCategory
from myapp.models.user import User
from myapp.services.file_service import FileService
from myapp.database.base import get_db
from myapp.auth.dependencies import (
    require_viewer_or_higher,
)
from myapp.utils.file_helpers import handle_file_not_found, delete_temp_file

router = APIRouter(tags=["Скачивание файлов"])


@router.get("/{file_id}/download", summary="Скачать файл")
async def get_download_file(
    file_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer_or_higher),
):
    """Скачать файл по его ID"""
    try:
        file_path, case_file = await FileService.get_for_download(session, file_id)

        return FileResponse(
            path=file_path,
            filename=case_file.original_name,
            media_type=case_file.mime_type,
        )

    except Exception as e:
        handle_file_not_found(e)


@router.post("/cases/{case_id}/archive", summary="Создать архив файлов случая")
async def create_case_archive(
    case_id: int,
    background_tasks: BackgroundTasks,
    category: Annotated[
        FileCategory, Form(description="Категория (primary/warranty/waybill)")
    ],
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer_or_higher),
):
    """Создать архив с файлами указанной категории"""
    try:
        archive_path = await FileService.create_archive(session, case_id, category)

        background_tasks.add_task(delete_temp_file, archive_path)
        return FileResponse(
            path=archive_path,
            filename=archive_path.name,
            media_type="application/zip",
        )

    except Exception as e:
        handle_file_not_found(e)
