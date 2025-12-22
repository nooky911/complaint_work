import asyncio
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from myapp.database.transactional import transactional
from myapp.validators.file_validator import FileValidator, MAX_CASE_SIZE
from myapp.services.storage_service import StorageService
from myapp.services.case_service import CaseService
from myapp.models.case_files import (
    CaseFile,
    FileCategory,
    WarrantyDocumentField,
)


class FileService:

    @staticmethod
    async def _get_total_case_size(session: AsyncSession, case_id: int) -> int:
        """Получить общий размер файлов случая"""
        stmt = select(func.sum(CaseFile.size_bytes)).where(CaseFile.case_id == case_id)
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def _process_single_file(
        session: AsyncSession,
        case_id: int,
        category: FileCategory,
        file: UploadFile,
        related_field: WarrantyDocumentField | None = None,
    ) -> CaseFile:
        """Внутренний метод для обработки одного файла: сохранение на диск и запись в БД"""
        # Генерация имен и путей
        stored_name = StorageService.generate_stored_name(file.filename)
        relative_file_path = StorageService.get_relative_path(
            case_id, category, stored_name, related_field
        )

        # Сохранение файла на сервер
        await StorageService.save_file_to_disk(file, relative_file_path)

        # Создание записи в БД
        case_file = CaseFile(
            case_id=case_id,
            category=category,
            related_field=related_field,
            original_name=file.filename,
            stored_name=stored_name,
            file_path=relative_file_path,
            mime_type=file.content_type,
            size_bytes=file.size,
        )

        session.add(case_file)
        await session.flush()

        return case_file

    @staticmethod
    async def get_file_by_id(session: AsyncSession, file_id: int) -> CaseFile | None:
        """Получить файл по ID"""
        stmt = select(CaseFile).where(CaseFile.id == file_id)
        result = await session.execute(stmt)

        return result.scalar_one_or_none()

    @staticmethod
    async def upload_file(
        session: AsyncSession,
        case_id: int,
        category: FileCategory,
        file: UploadFile,
        related_field: WarrantyDocumentField | None = None,
    ) -> CaseFile:
        """Загрузка одного файла"""
        results = await FileService.upload_files(
            session, case_id, category, [file], related_field
        )
        return results[0]

    @staticmethod
    @transactional
    async def upload_files(
        session: AsyncSession,
        case_id: int,
        category: FileCategory,
        files: list[UploadFile],
        related_field: WarrantyDocumentField | None = None,
    ) -> list[CaseFile]:
        """Загрузка нескольких файлов"""
        if related_field == "" or related_field == "string":
            related_field = None

        case = await CaseService.get_case(session, case_id)
        if not case:
            raise ValueError(f"Случай с ID {case_id} не найден")

        if category == FileCategory.warranty and not related_field:
            raise ValueError("Для warranty файлов обязателен related_field")
        if category == FileCategory.primary and related_field is not None:
            raise ValueError("Для primary файлов related_field должен быть None")

        total_case_size = await FileService._get_total_case_size(session, case_id)
        total_new_size = 0
        for file in files:
            if file.size is None:
                file.file.seek(0, 2)
                file.size = file.file.tell()
                file.file.seek(0)

            total_new_size += file.size

        if total_case_size + total_new_size > MAX_CASE_SIZE:
            raise ValueError(
                f"Превышен общий лимит размера для случая ({MAX_CASE_SIZE // (1024*1024)} МБ)"
            )

        uploaded_files = []

        try:
            for file in files:
                FileValidator.validate_file(file, category)

                case_file = await FileService._process_single_file(
                    session, case_id, category, file, related_field
                )
                uploaded_files.append(case_file)

            await session.flush()

            return uploaded_files

        except Exception as e:
            for case_file in uploaded_files:
                try:
                    full_path = StorageService.get_full_path(case_file)
                    if full_path.exists():
                        await asyncio.to_thread(full_path.unlink)
                except Exception:
                    pass
            raise e

    @staticmethod
    @transactional
    async def delete_file(session: AsyncSession, file_id: int) -> int:
        """Удаление файла"""
        case_file = await FileService.get_file_by_id(session, file_id)
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
        """Получить путь к файлу и модель CaseFile для скачивания"""
        case_file = await FileService.get_file_by_id(session, file_id)

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
    async def create_archive(
        session: AsyncSession,
        case_id: int,
        category: FileCategory,
    ) -> Path:
        """Создать архив с файлами"""
        files = await FileService.get_files_by_case(session, case_id, category)

        if not files:
            raise FileNotFoundError(f"Файлов для категории {category.value} не найдено")

        return await StorageService.create_archive(case_id, category, files)
