from fastapi import APIRouter

from app.backend.api.endpoints import auth, cases

router = APIRouter(prefix="/api")

router.include_router(auth.router)
router.include_router(cases.router)