# 회원가입 / 로그인 엔드포인트
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.backend.utils.dependencies import get_current_user, get_db
from app.backend.models.user import User
from app.backend.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.backend.services.auth_service import create_user, get_user_by_username, verify_password
from app.backend.utils.jwt_handler import create_access_token, create_refresh_token
from app.com.logger import get_logger

logger = get_logger("auth")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = create_user(db, body.username, body.password)
    except ValueError as e:
        # 아이디 중복인 경우 409 반환
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    # 유저 조회
    user = get_user_by_username(db, body.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
        )

    # 비밀번호 확인
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
        )

    # 토큰 생성
    access_token = create_access_token(user.id, user.username)
    refresh_token = create_refresh_token(user.id)

    # Refresh 토큰 DB 저장
    user.refresh_token = refresh_token
    db.commit()

    logger.info(f"로그인 완료 - username: {user.username}")

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Refresh 토큰을 null 로 덮어써서 재발급 불가 상태로 만듦
    current_user.refresh_token = None
    db.commit()

    logger.info(f"로그아웃 완료 - username: {current_user.username}")

    return {"message": "로그아웃 완료"}