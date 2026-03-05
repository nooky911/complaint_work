from pathlib import Path
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
    _current_user: User = Depends(require_viewer_or_higher),
):
    """Скачать файл по его ID"""
    try:
        file_path, case_file = await FileService.get_for_download(session, file_id)

        # Временный файл для корректной отправки имени
        temp_file = Path(file_path.parent / f"temp_{case_file.original_name}")
        temp_file.write_bytes(file_path.read_bytes())

        response = FileResponse(
            path=temp_file,
            filename=case_file.original_name,
            media_type=case_file.mime_type,
        )

        background_tasks.add_task(delete_temp_file, temp_file)

        return response

    except Exception as e:
        handle_file_not_found(e)


@router.post("/cases/{case_id}/archive", summary="Создать архив файлов случая")
async def create_case_archive(
    case_id: int,
    category: Annotated[FileCategory, Form(description="Категория файлов для архива")],
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_viewer_or_higher),
):
    """Создать архив с файлами указанной категории"""
    try:
        archive_path = await FileService.create_archive(session, case_id, category)

        return FileResponse(
            path=archive_path,
            filename=archive_path.name,
            media_type="application/zip",
        )

    except Exception as e:
        handle_file_not_found(e)
