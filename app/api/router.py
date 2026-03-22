# 전체 라우터를 한곳에 모아서 관리하는 파일
from fastapi import APIRouter

from app.api.endpoints import auth

router = APIRouter(prefix="/api")

router.include_router(auth.router)
