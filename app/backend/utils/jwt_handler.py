# JWT 토큰 발급 및 검증
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings
from app.com.logger import get_logger

logger = get_logger("jwt_handler")


def create_access_token(user_id: int, username: str) -> str:
    # 만료 시각 계산 (현재 시각 + 30분)
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user_id),   # 토큰 주인 (user_id)
        "username": username,
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int, username: str) -> str:
    # 만료 시각 계산 (현재 시각 + 7일)
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    # 토큰을 검증하고 안에 담긴 정보를 꺼냄
    # 만료됐거나 서명이 틀리면 JWTError 발생
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        logger.info("토큰 검증 실패 - 만료되었거나 유효하지 않은 토큰")
        raise
