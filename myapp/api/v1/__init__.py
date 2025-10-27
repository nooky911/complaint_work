from fastapi import APIRouter

from .endpoints.__init__ import endpoints_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(endpoints_router)