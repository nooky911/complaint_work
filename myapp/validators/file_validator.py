from fastapi import UploadFile

from myapp.schemas.files import FileCategory

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 Мб
MAX_CASE_SIZE = 50 * 1024 * 1024  # 50 Мб

ALLOWED_MIME_TYPES = {
    # Общие разрешенные типы для ВСЕЙ первичной документации
    FileCategory.primary: {
        # --- Фото ---
        "image/jpeg",
        "image/png",
        # --- Документы ---
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/csv",
        "application/rtf",
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
        "application/x-rar-compressed",
        "application/x-7z-compressed",
        # Письма Outlook
        "application/vnd.ms-outlook",
    },
    # Типы для рекламационной работы
    FileCategory.warranty: {
        "application/pdf",
        "image/jpeg",
        "application/vnd.ms-outlook",
    },
}


class FileValidator:

    @staticmethod
    def validate_mime_type(file: UploadFile, category: FileCategory):
        """Валидация на расширение"""
        allowed_types = ALLOWED_MIME_TYPES[category]
        if file.content_type not in allowed_types:
            raise ValueError(
                f"Неподдерживаемый формат файла для категории {category.value}"
            )

    @staticmethod
    def validate_not_empty(file: UploadFile):
        """Валидация на пустой файл"""
        if file.size == 0:
            raise ValueError("Файл не должен быть пустым")

    @staticmethod
    def validate_file_size(file: UploadFile, max_size: int = MAX_FILE_SIZE):
        """Валидация по размеру файла"""
        if file.size > max_size:
            raise ValueError(f"Размер файла превышает {max_size}")

    @staticmethod
    def validate_file(file: UploadFile, category: FileCategory):
        """Комплексная валидация файла"""
        FileValidator.validate_not_empty(file)
        FileValidator.validate_file_size(file)
        FileValidator.validate_mime_type(file, category)
