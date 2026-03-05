import logging
from pathlib import Path
from fastapi import HTTPException, status


def handle_file_not_found(e: Exception):
    """Преобразует исключение FileNotFoundError в HTTP 404, остальное 500 с логированием"""
    if isinstance(e, FileNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    logger = logging.getLogger(__name__)
    logger.error("Unexpected error in file endpoint", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Произошла непредвиденная ошибка сервера: {type(e).__name__}",
    )


def delete_temp_file(file_path: Path):
    """Удаляет временный файл после отправки"""
    try:
        file_path.unlink(missing_ok=True)
    except Exception:
        pass
