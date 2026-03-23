from fastapi import APIRouter

from app.backend.api.endpoints import auth

router = APIRouter(prefix="/api")

router.include_router(auth.router)