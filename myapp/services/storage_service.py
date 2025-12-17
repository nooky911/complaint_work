import uuid
import tempfile
import zipfile
import asyncio
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile

from myapp.config import settings
from myapp.models.case_files import (
    CaseFile,
    FileCategory,
    WarrantyDocumentField,
)

BASE_STORAGE_PATH: Path = Path(settings.FILE_STORAGE_PATH)

if not BASE_STORAGE_PATH.exists():
    BASE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


class StorageService:
    """Сервис для построения путей на диске"""

    @staticmethod
    def _sync_create_archive(
        case_id: int, category: FileCategory, files: list[CaseFile]
    ) -> Path:
        """Создание ZIP-архива"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if category == FileCategory.PRIMARY:
            archive_name = f"Первичные_документы_случая_{case_id}_{timestamp}.zip"
        else:
            archive_name = f"Рекламационные_документы_случая_{case_id}_{timestamp}.zip"

        archive_path = Path(tempfile.gettempdir()) / archive_name

        try:
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                used_names = set()

                for case_file in files:
                    file_path = StorageService.get_full_path(case_file)

                    if file_path.exists():
                        original_name = case_file.original_name
                        arc_name = original_name
                        counter = 1

                        # Решение проблемы одинаковых названий файлов
                        while arc_name in used_names:
                            name_parts = original_name.rsplit(".", 1)
                            name_without_ext = name_parts[0]
                            extension = (
                                "." + name_parts[1] if len(name_parts) == 2 else ""
                            )

                            arc_name = f"{name_without_ext}({counter}){extension}"
                            counter += 1

                        used_names.add(arc_name)
                        zipf.write(file_path, arc_name)

            return archive_path

        except Exception:
            if archive_path.exists():
                archive_path.unlink()
            raise

    @staticmethod
    def generate_stored_name(original_name: str) -> str:
        """Генерация уникального имени"""
        original_path = Path(original_name)

        file_extension = original_path.suffix.lower()
        unique_id = uuid.uuid4().hex[:16]
        timestamp = int(datetime.now().timestamp())

        if file_extension:
            return f"{unique_id}_{timestamp}{file_extension}"
        else:
            return f"{unique_id}_{timestamp}"

    @staticmethod
    def get_relative_path(
        case_id: int,
        category: FileCategory,
        stored_name: str,
        related_field: WarrantyDocumentField | None = None,
    ) -> str:
        """Относительный путь для хранения файла"""
        case_id_str = str(case_id)

        relative_path_base = Path("cases") / case_id_str

        if category == FileCategory.PRIMARY:
            relative_path = relative_path_base / "primary" / stored_name
        elif category == FileCategory.WARRANTY and related_field:
            field_value = str(related_field.value)
            relative_path = relative_path_base / "warranty" / field_value / stored_name
        else:
            raise ValueError(
                f"Некорректные параметры: category={category}, related_field={related_field}"
            )

        if any(part in (".", "..") for part in relative_path.parts):
            raise ValueError("Недопустимый путь")

        return relative_path.as_posix()

    @staticmethod
    def get_full_path(path_or_model: str | CaseFile) -> Path:
        """Получить полный путь к файлу на диске"""
        if isinstance(path_or_model, CaseFile):
            relative_path_str = path_or_model.file_path
        else:
            relative_path_str = path_or_model

        full_path = BASE_STORAGE_PATH / relative_path_str

        full_path.parent.mkdir(parents=True, exist_ok=True)

        return full_path

    @staticmethod
    async def save_file_to_disk(file: UploadFile, relative_path: str) -> None:
        """Сохранение загруженного файла на диск"""
        try:
            content = await file.read()
            full_path = StorageService.get_full_path(relative_path)
            await asyncio.to_thread(full_path.write_bytes, content)
        finally:
            await file.close()

    @staticmethod
    async def create_archive(
        case_id: int, category: FileCategory, files: list[CaseFile]
    ) -> Path:
        """Выносим блокирующую операцию в отдельный поток"""
        return await asyncio.to_thread(
            StorageService._sync_create_archive, case_id, category, files
        )
