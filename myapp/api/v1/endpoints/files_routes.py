from fastapi import APIRouter

from myapp.api.v1.endpoints.files.upload_routes import router as upload_router
from myapp.api.v1.endpoints.files.download_routes import router as download_router
from myapp.api.v1.endpoints.files.management_routes import router as management_router

router = APIRouter(prefix="/files", tags=["Файлы случая неисправности"])


router.include_router(upload_router)
router.include_router(download_router)
router.include_router(management_router)
