from fastapi import APIRouter

from .case_routes import router as case_router
from .references_routes import router as references_router
from .auth_routes import router as auth_router
from .user_routes import router as user_router
from .files_routes import router as files_router
from .warranty_routes import router as warranty_router

endpoints_router = APIRouter()

endpoints_router.include_router(auth_router)  # /auth/**
endpoints_router.include_router(user_router)  # /users/**
endpoints_router.include_router(case_router)  # /cases/** (включает warranty_router)
endpoints_router.include_router(files_router)  # /files/**
endpoints_router.include_router(references_router)  # /references/**
