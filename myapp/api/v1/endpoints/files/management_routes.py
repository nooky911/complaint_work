from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.models.case_files import FileCategory
from myapp.models.user import User
from myapp.services.file_service import FileService
from myapp.database.base import get_db
from myapp.schemas.files import FileInfo
from myapp.auth.dependencies import (
    require_viewer_or_higher,
    require_can_edit_file_case,
)
from myapp.utils.file_helpers import handle_file_not_found

router = APIRouter(tags=["Управление файлами"])


@router.get(
    "/cases/{case_id}",
    response_model=list[FileInfo],
    summary="Получить список файлов случая для UI",
)
async def get_case_files(
    case_id: int,
    category: Annotated[
        FileCategory | None,
        None,
    ] = None,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_viewer_or_higher),
):
    """Получить список файлов случая с опциональной фильтрацией по категории"""
    try:
        return await FileService.get_files_by_case(session, case_id, category)
    except Exception as e:
        handle_file_not_found(e)


@router.get(
    "/cases/{case_id}/grouped",
    response_model=dict,
    summary="Получить файлы случая, разбитые по типам документов",
)
async def get_case_files_grouped(
    case_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_viewer_or_higher),
):
    """Возвращает все файлы случая, сгруппированные по категории случая (primary/warranty)"""
    try:
        return await FileService.get_files_by_case_cached(session, case_id)
    except Exception as e:
        handle_file_not_found(e)


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить файл",
)
async def delete_file(
    file_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_can_edit_file_case),
):
    """Удалить файл по ID"""
    try:
        deleted_count = await FileService.delete_file(session, file_id)
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл не найден",
            )
        return None
    except Exception as e:
        handle_file_not_found(e)
