import logging
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    Form,
    File,
    Query,
)
from fastapi.background import BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from pathlib import Path

from myapp.models.case_files import FileCategory, WarrantyDocumentField
from myapp.models.user import User
from myapp.services.file_service import FileService
from myapp.database.base import get_db
from myapp.schemas.files import FileInfo
from myapp.auth.dependencies import (
    require_can_edit_case,
    require_viewer_or_higher,
    require_can_edit_file_case,
)

router = APIRouter(prefix="/files", tags=["Файлы случая неисправности"])
logger = logging.getLogger(__name__)


def handle_file_not_found(e: Exception):
    """Преобразует исключение FileNotFoundError в HTTP 404, остальное – 500 с логированием"""
    if isinstance(e, FileNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    logger.error("Unexpected error in file endpoint", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Произошла непредвиденная ошибка сервера: {type(e).__name__}",
    )


def delete_temp_file(file_path: Path):
    """Удаляет временный файл после отправки"""
    try:
        file_path.unlink(missing_ok=True)
    except Exception:
        pass


@router.post(
    "/cases/{case_id}/upload",
    response_model=FileInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузка одного файла (Primary/Warranty)",
)
async def upload_single_file(
    case_id: int,
    category: Annotated[
        FileCategory, Form(description="Категория файла (primary/warranty)")
    ],
    file: Annotated[UploadFile, File(description="Файл для загрузки")],
    related_field: Annotated[
        WarrantyDocumentField | None, Form(description="Поле для warranty файлов")
    ] = None,
    session: AsyncSession = Depends(get_db),
    _user_and_case=Depends(require_can_edit_case),
):
    """
    Загрузка первичного файла для случая неисправности.

    Поддерживаемые форматы: документы, фото, видео, архивы.
    Максимальный размер файла: 15 МБ.
    """
    try:
        case_file = await FileService.upload_file(
            session=session,
            case_id=case_id,
            category=category,
            file=file,
            related_field=related_field,
        )
        return case_file
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        handle_file_not_found(e)


@router.post(
    "/cases/{case_id}/upload-files",
    response_model=list[FileInfo],
    status_code=status.HTTP_201_CREATED,
    summary="Загрузка нескольких файлов",
)
async def upload_multiple_files(
    case_id: int,
    category: Annotated[FileCategory, Form()],
    files: Annotated[list[UploadFile], File()],
    related_field: Annotated[WarrantyDocumentField | None, Form()] = None,
    session: AsyncSession = Depends(get_db),
    _user_and_case=Depends(require_can_edit_case),
):
    """Загрузка нескольких файлов"""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо предоставить хотя бы один файл",
        )

    try:
        uploaded_files = await FileService.upload_files(
            session=session,
            case_id=case_id,
            category=category,
            files=files,
            related_field=related_field,
        )
        return uploaded_files
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        handle_file_not_found(e)


@router.get(
    "/cases/{case_id}",
    response_model=list[FileInfo],
    summary="Получить список файлов случая для UI",
)
async def get_case_files(
    case_id: int,
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer_or_higher),
):
    """Получить список всех файлов случая для отображения в UI"""
    try:
        files = await FileService.get_files_by_case(session, case_id)
        return files
    except Exception as e:
        handle_file_not_found(e)


@router.get("/{file_id}/download", summary="Скачать файл")
async def get_download_file(
    file_id: int,
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer_or_higher),
) -> FileResponse:
    """Скачать файл по его ID"""
    try:
        file_path, case_file = await FileService.get_for_download(session, file_id)

        return FileResponse(
            path=file_path,
            filename=case_file.original_name,
            media_type=case_file.mime_type or "application/octet-stream",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при скачивании файла: {str(e)}",
        )


@router.post("/cases/{case_id}/archive", summary="Создать архив файлов случая")
async def create_case_archive(
    case_id: int,
    category: Annotated[
        FileCategory,
        Query(description="Категория файлов для архива (primary/warranty)"),
    ],
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(require_viewer_or_higher),
) -> FileResponse:
    """Создать ZIP-архив со всеми файлами указанной категории для случая"""
    try:
        archive_path = await FileService.create_archive(session, case_id, category)

        archive_name = archive_path.name

        background_tasks.add_task(delete_temp_file, archive_path)

        return FileResponse(
            path=archive_path,
            filename=archive_name,
            media_type="application/zip",
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании архива: {str(e)}",
        )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить файл",
)
async def delete_file(
    file_id: int,
    session: AsyncSession = Depends(get_db),
    _user_and_case=Depends(require_can_edit_file_case),
):
    """Удалить файл по его ID"""
    try:
        deleted_count = await FileService.delete_file(session, file_id)

        if not deleted_count:
            raise FileNotFoundError(f"Файл с ID {file_id} не найден")

        return None

    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        handle_file_not_found(e)
