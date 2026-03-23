# 회원가입 / 로그인 API 입출력 규격
from datetime import datetime

from pydantic import BaseModel, Field


# 회원가입 요청 데이터
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="로그인에 사용할 아이디 (3~50자)")
    password: str = Field(min_length=8, max_length=72, description="비밀번호 (8~72자)")


# 로그인 요청 데이터
class LoginRequest(BaseModel):
    username: str
    password: str


# 회원가입 성공 시 반환 데이터
class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    # DB 모델을 바로 넣어도 변환되도록 설정
    model_config = {"from_attributes": True}


# 로그인 성공 시 반환 데이터
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# 리프레시 토큰 재발급 요청 데이터
class RefreshRequest(BaseModel):
    refresh_token: str


# 액세스 토큰 재발급 성공 시 반환 데이터
class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
