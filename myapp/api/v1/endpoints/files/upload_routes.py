from fastapi import (
    APIRouter,
    Depends,
    status,
    UploadFile,
    Form,
    File,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from myapp.models.case_files import FileCategory, WarrantyDocumentField
from myapp.models.user import User
from myapp.services.file_service import FileService
from myapp.database.base import get_db
from myapp.schemas.files import FileInfo
from myapp.auth.dependencies import (
    require_can_edit_case,
)
from myapp.utils.file_helpers import handle_file_not_found

router = APIRouter(tags=["Загрузка файлов"])


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
    related_field: Annotated[
        WarrantyDocumentField | None,
        Form(description="Поле для warranty файлов"),
    ] = None,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_can_edit_case),
):
    """Загрузка одного файла с указанием категории и related_field для warranty"""
    try:
        return await FileService.upload_file(
            session, case_id, category, file, related_field
        )
    except Exception as e:
        handle_file_not_found(e)


@router.post(
    "/cases/{case_id}/upload-files",
    response_model=list[FileInfo],
    status_code=status.HTTP_201_CREATED,
    summary="Загрузка нескольких файлов одной категории",
)
async def upload_multiple_files(
    case_id: int,
    category: Annotated[
        FileCategory, Form(description="Категория файлов (primary/warranty)")
    ],
    related_field: Annotated[
        WarrantyDocumentField | None,
        Form(description="Поле для warranty файлов"),
    ] = None,
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_can_edit_case),
):
    """Загрузка нескольких файлов одной категории"""
    try:
        return await FileService.upload_files(
            session, case_id, category, files, related_field
        )
    except Exception as e:
        handle_file_not_found(e)
