from fastapi import APIRouter

from .case_routes import router as case_router
from .warranty_routes import router as warranty_router

endpoints_router = APIRouter()

case_router.include_router(warranty_router)

endpoints_router.include_router(case_router)
