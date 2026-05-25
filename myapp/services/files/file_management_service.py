import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from myapp.database.transactional import transactional
from myapp.services.storage_service import StorageService
from myapp.models.case_files import (
    CaseFile,
    FileCategory,
    WarrantyDocumentField,
    WaybillDocumentField,
)
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
        """Удаление файла (проверяет, есть ли другие ссылки на этот файл на диске)"""

        case_file = await FileManagementService.get_file_by_id(session, file_id)
        if not case_file:
            return 0

        stmt = (
            select(func.count())
            .select_from(CaseFile)
            .where(CaseFile.file_path == case_file.file_path)
        )
        usage_count = await session.execute(stmt)
        count = usage_count.scalar() or 0

        delete_stmt = delete(CaseFile).where(CaseFile.id == file_id)
        result = await session.execute(delete_stmt)
        await session.flush()

        if result.rowcount and count <= 1:
            full_path = StorageService.get_full_path(case_file)
            try:
                await asyncio.to_thread(full_path.unlink, missing_ok=True)
            except FileNotFoundError:
                pass

        return result.rowcount  # type: ignore

    @staticmethod
    async def search_unique_files(
        session: AsyncSession,
        category: FileCategory,
        related_field: str | None = None,
        search_query: str | None = None,
        limit: int = 50,
    ) -> list[CaseFile]:
        """Поиск уникальных файлов для выбора"""

        stmt = select(CaseFile).distinct(CaseFile.file_path)

        conditions = [CaseFile.category == category]
        if related_field:
            conditions.append(CaseFile.related_field == related_field)

        if search_query:
            conditions.append(CaseFile.original_name.ilike(f"%{search_query}%"))

        stmt = (
            stmt.where(*conditions)
            .order_by(CaseFile.file_path, CaseFile.id.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    @transactional
    async def link_existing_file(
        session: AsyncSession,
        case_id: int,
        existing_file_id: int,
        category: FileCategory,
        related_field: WarrantyDocumentField | WaybillDocumentField | None = None,
    ) -> CaseFile:
        """Создает ссылку на уже существующий файл для нового случая"""

        existing_file = await FileManagementService.get_file_by_id(
            session, existing_file_id
        )
        if not existing_file:
            raise ValueError(f"Исходный файл с ID {existing_file_id} не найден")

        new_file = CaseFile(
            case_id=case_id,
            category=category,
            related_field=related_field,
            original_name=existing_file.original_name,
            stored_name=existing_file.stored_name,
            file_path=existing_file.file_path,
            mime_type=existing_file.mime_type,
            size_bytes=existing_file.size_bytes,
        )

        session.add(new_file)
        await session.flush()
        return new_file

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
        """Получить все файлы случая, сгруппированные по категориям"""
        all_files = await FileManagementService.get_files_by_case(session, case_id)

        all_files_dict = [FileInfo.model_validate(file) for file in all_files]

        grouped_files = {}
        warranty_files = []
        waybill_files = []

        for file in all_files_dict:
            if file.category in ("warranty", "waybill") and file.related_field:
                if file.related_field not in grouped_files:
                    grouped_files[file.related_field] = []
                grouped_files[file.related_field].append(file)

                if file.category == "warranty":
                    warranty_files.append(file)
                elif file.category == "waybill":
                    waybill_files.append(file)

            else:
                if "primary" not in grouped_files:
                    grouped_files["primary"] = []
                grouped_files["primary"].append(file)

        if warranty_files:
            grouped_files["all_warranty"] = warranty_files

        if waybill_files:
            grouped_files["all_waybill"] = waybill_files

        return grouped_files
