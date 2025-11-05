from fastapi import APIRouter

from .case_routes import router as case_router
from .references_routes import router as references_router

endpoints_router = APIRouter()

endpoints_router.include_router(case_router)
endpoints_router.include_router(references_router)