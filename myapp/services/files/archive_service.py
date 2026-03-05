from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.services.storage_service import StorageService
from myapp.models.case_files import FileCategory
from myapp.services.files.file_management_service import FileManagementService


class FileArchiveService:
    """Сервис для создания архивов файлов"""

    @staticmethod
    async def create_archive(
        session: AsyncSession,
        case_id: int,
        category: FileCategory,
    ) -> Path:
        """Создать архив с файлами"""
        files = await FileManagementService.get_files_by_case(
            session, case_id, category
        )

        if not files:
            raise FileNotFoundError(f"Файлов для категории {category.value} не найдено")

        return await StorageService.create_archive(case_id, category, files)
