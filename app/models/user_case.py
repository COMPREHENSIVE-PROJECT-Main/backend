# 사용자가 입력한 사건과 유저 테이블
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func

from app.database import Base


class UserCase(Base):
    __tablename__ = "user_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # data/input_cases/ JSON 파일의 case_id와 연결 ex) case_0001
    case_id = Column(String(50), nullable=False, unique=True)

    # 이 사건을 입력한 유저
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    