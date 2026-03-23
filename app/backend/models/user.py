# 유저 정보를 저장하는 users 테이블
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func

from app.backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    username = Column(String(50), nullable=False, unique=True)

    # bcrypt로 암호화된 비밀번호 넣어야 함
    hashed_password = Column(String(255), nullable=False)

    # Refresh 토큰 - 로그아웃 시 null로 덮어써서 무효화
    refresh_token = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
