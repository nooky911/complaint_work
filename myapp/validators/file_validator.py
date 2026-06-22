from fastapi import UploadFile

from myapp.schemas.files import FileCategory

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 Мб
MAX_CASE_SIZE = 50 * 1024 * 1024  # 50 Мб

DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.ms-outlook",
    "application/x-ole-storage",
    "application/octet-stream",
}

ALLOWED_MIME_TYPES = {
    # Общие разрешенные типы для ВСЕЙ первичной документации
    FileCategory.primary: {
        # --- Фото ---
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/jfif",
        "image/pjpeg",
        # --- Документы ---
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/csv",
        "application/rtf",
        "application/x-rpm",
        # --- Видео ---
        "video/mp4",
        "video/mpeg",
        "video/avi",
        "video/x-msvideo",
        "video/quicktime",
        "video/x-ms-wmv",
        "video/webm",
        "video/3gpp",
        # --- Архивы ---
        "application/zip",
        "application/x-zip-compressed",
        "application/zip-compressed",
        "application/x-rar-compressed",
        "application/vnd.rar",
        "application/x-7z-compressed",
        # Письма Outlook
        "application/vnd.ms-outlook",
        "application/x-ole-storage",
        "application/octet-stream",
    },
    # Типы для рекламационной работы
    FileCategory.warranty: DOCUMENT_MIME_TYPES,
    # Типы для ТТН
    FileCategory.waybill: DOCUMENT_MIME_TYPES,
}


class FileValidator:

    @staticmethod
    def validate_mime_type(file: UploadFile, category: FileCategory) -> None:
        """Валидация на расширение"""
        allowed_types = ALLOWED_MIME_TYPES[category]
        if file.content_type not in allowed_types:
            raise ValueError(
                f"Неподдерживаемый формат файла для категории {category.value}"
            )

    @staticmethod
    def validate_not_empty(file: UploadFile) -> None:
        """Валидация на пустой файл"""
        if file.size == 0:
            raise ValueError("Файл не должен быть пустым")

    @staticmethod
    def validate_file_size(file: UploadFile, max_size: int = MAX_FILE_SIZE) -> None:
        """Валидация по размеру файла"""
        if file.size > max_size:
            raise ValueError(f"Размер файла превышает {max_size}")

    @staticmethod
    def validate_file(file: UploadFile, category: FileCategory) -> None:
        """Комплексная валидация файла"""
        FileValidator.validate_not_empty(file)
        FileValidator.validate_file_size(file)
        FileValidator.validate_mime_type(file, category)
