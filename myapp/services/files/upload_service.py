from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from myapp.database.transactional import transactional
from myapp.validators.file_validator import FileValidator, MAX_CASE_SIZE
from myapp.services.storage_service import StorageService
from myapp.services.case_service import CaseService
from myapp.models.case_files import (
    CaseFile,
    FileCategory,
    WarrantyDocumentField,
)


class FileUploadService:
    """Сервис для загрузки файлов"""

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
    async def upload_file(
        session: AsyncSession,
        case_id: int,
        category: FileCategory,
        file: UploadFile,
        related_field: WarrantyDocumentField | None = None,
    ) -> CaseFile:
        """Загрузка одного файла"""
        results = await FileUploadService.upload_files(
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

        total_case_size = await FileUploadService._get_total_case_size(session, case_id)
        total_new_size = 0
        for file in files:
            content = await file.read()
            f_size = len(content)
            await file.seek(0)
            total_new_size += f_size

        if total_case_size + total_new_size > MAX_CASE_SIZE:
            raise ValueError(
                f"Превышен общий лимит размера для случая ({MAX_CASE_SIZE // (1024*1024)} МБ)"
            )

        uploaded_files = []

        try:
            for file in files:
                FileValidator.validate_file(file, category)

                case_file = await FileUploadService._process_single_file(
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
                        full_path.unlink()
                except Exception as cleanup_err:
                    print(
                        f"Ошибка при удалении файла {case_file.original_name}: {cleanup_err}"
                    )
            raise e
