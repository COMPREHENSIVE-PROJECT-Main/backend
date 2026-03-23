# 엔드포인트에 주입되는 공통 의존성 모음
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.backend.models.user import User
from app.backend.services.auth_service import get_user_by_username
from app.backend.db.database import SessionLocal
from app.backend.utils.jwt_handler import decode_token
from app.com.logger import get_logger

logger = get_logger("dependencies")

# Authorization 헤더에서 Bearer 토큰을 꺼내주는 객체
bearer_scheme = HTTPBearer()


def get_db() -> Generator:
    # 요청마다 DB 세션을 열고 끝나면 자동으로 닫음
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    # 토큰 검증 실패 시 공통으로 던질 에러
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="토큰이 유효하지 않거나 만료되었습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 헤더에서 꺼낸 토큰을 검증하고 payload 추출
        payload = decode_token(credentials.credentials)

        # 액세스 토큰인지 확인 (리프레시 토큰으로 API 접근 방지)
        if payload.get("type") != "access":
            raise credentials_error

        username: str = payload.get("username")
        if username is None:
            raise credentials_error

    except JWTError:
        raise credentials_error

    # 토큰의 username 으로 실제 유저 조회
    user = get_user_by_username(db, username)
    if user is None:
        logger.info(f"토큰은 유효하지만 유저를 찾을 수 없음 - username: {username}")
        raise credentials_error

    return user
