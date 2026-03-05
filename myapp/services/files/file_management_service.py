import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from myapp.database.transactional import transactional
from myapp.services.storage_service import StorageService
from myapp.models.case_files import CaseFile, FileCategory
from myapp.schemas.files import FileInfo


class FileManagementService:
    """Сервис для управления файлами"""

    @staticmethod
    async def get_file_by_id(session: AsyncSession, file_id: int) -> CaseFile | None:
        """Получить файл по ID"""
        stmt = select(CaseFile).where(CaseFile.id == file_id)
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    @transactional
    async def delete_file(session: AsyncSession, file_id: int) -> int:
        """Удаление файла"""
        case_file = await FileManagementService.get_file_by_id(session, file_id)
        if not case_file:
            return 0

        stmt = delete(CaseFile).where(CaseFile.id == file_id)
        result = await session.execute(stmt)

        if result.rowcount:  # type: ignore
            full_path = StorageService.get_full_path(case_file)
            try:
                await asyncio.to_thread(full_path.unlink)
            except FileNotFoundError:
                pass

        return result.rowcount  # type: ignore

    @staticmethod
    async def get_for_download(
        session: AsyncSession, file_id: int
    ) -> tuple[Path, CaseFile]:
        """Получить кортеж из пути к файлу и объекта БД для скачивания"""
        case_file = await FileManagementService.get_file_by_id(session, file_id)

        if not case_file:
            raise FileNotFoundError(f"Файл с ID {file_id} не найден в базе данных")

        full_path = StorageService.get_full_path(case_file)

        if not full_path.exists():
            raise FileNotFoundError(f"Файл с ID {file_id} не найден на диске")

        return full_path, case_file

    @staticmethod
    async def get_files_by_case(
        session: AsyncSession,
        case_id: int,
        category: FileCategory | None = None,
    ) -> list[CaseFile]:
        """Получить список файлов случая (для отображения в UI)"""
        condition = [CaseFile.case_id == case_id]

        if category:
            condition.append(CaseFile.category == category)

        stmt = select(CaseFile).where(*condition).order_by(CaseFile.id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_files_by_case_cached(
        session: AsyncSession,
        case_id: int,
    ) -> dict[str, list]:
        """Получить все файлы случая, сгруппированные по related_field для быстрого доступа"""
        all_files = await FileManagementService.get_files_by_case(session, case_id)

        all_files_dict = [FileInfo.model_validate(file) for file in all_files]

        grouped_files = {}
        warranty_files = []

        for file in all_files_dict:
            if file.category == "warranty":
                if file.related_field not in grouped_files:
                    grouped_files[file.related_field] = []
                grouped_files[file.related_field].append(file)
                warranty_files.append(file)
            else:
                if "primary" not in grouped_files:
                    grouped_files["primary"] = []
                grouped_files["primary"].append(file)

        if warranty_files:
            grouped_files["all_warranty"] = warranty_files

        return grouped_files
