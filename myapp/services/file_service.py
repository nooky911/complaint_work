from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.case_files import (
    CaseFile,
    FileCategory,
    WarrantyDocumentField,
)
from myapp.services.files.upload_service import FileUploadService
from myapp.services.files.file_management_service import FileManagementService
from myapp.services.files.archive_service import FileArchiveService


class FileService:
    """Основной сервис для работы с файлами - фасад для специализированных сервисов"""

    @staticmethod
    async def get_file_by_id(session: AsyncSession, file_id: int) -> CaseFile | None:
        """Получить файл по ID"""
        return await FileManagementService.get_file_by_id(session, file_id)

    @staticmethod
    async def upload_file(
        session: AsyncSession,
        case_id: int,
        category: FileCategory,
        file: UploadFile,
        related_field: WarrantyDocumentField | None = None,
    ) -> CaseFile:
        """Загрузка одного файла"""
        return await FileUploadService.upload_file(
            session, case_id, category, file, related_field
        )

    @staticmethod
    async def upload_files(
        session: AsyncSession,
        case_id: int,
        category: FileCategory,
        files: list[UploadFile],
        related_field: WarrantyDocumentField | None = None,
    ) -> list[CaseFile]:
        """Загрузка нескольких файлов"""
        return await FileUploadService.upload_files(
            session, case_id, category, files, related_field
        )

    @staticmethod
    async def delete_file(session: AsyncSession, file_id: int) -> int:
        """Удаление файла"""
        return await FileManagementService.delete_file(session, file_id)

    @staticmethod
    async def get_for_download(
        session: AsyncSession, file_id: int
    ) -> tuple[Path, CaseFile]:
        """Получить путь к файлу и модель CaseFile для скачивания"""
        return await FileManagementService.get_for_download(session, file_id)

    @staticmethod
    async def get_files_by_case(
        session: AsyncSession,
        case_id: int,
        category: FileCategory | None = None,
    ) -> list[CaseFile]:
        """Получить список файлов случая (для отображения в UI)"""
        return await FileManagementService.get_files_by_case(session, case_id, category)

    @staticmethod
    async def get_files_by_case_cached(
        session: AsyncSession,
        case_id: int,
    ) -> dict[str, list]:
        """Получить все файлы случая, сгруппированные по related_field для быстрого доступа"""
        return await FileManagementService.get_files_by_case_cached(session, case_id)

    @staticmethod
    async def create_archive(
        session: AsyncSession,
        case_id: int,
        category: FileCategory,
    ) -> Path:
        """Создать архив с файлами"""
        return await FileArchiveService.create_archive(session, case_id, category)
