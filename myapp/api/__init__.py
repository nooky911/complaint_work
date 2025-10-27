from fastapi import APIRouter

from .v1.__init__ import v1_router

api_router = APIRouter(prefix="/api")

api_router.include_router(v1_router)