# 판례 데이터를 저장하는 cases 테이블 모델
from sqlalchemy import Column, String, Text, Date, TIMESTAMP, func

from app.database import Base


class Case(Base):
    __tablename__ = "cases"

    # 사건번호 - 기본키
    case_id = Column(String(50), primary_key=True, nullable=False)

    # 사건명
    case_name = Column(String(255), nullable=False)

    # 법원명
    court = Column(String(100), nullable=False)

    # 선고일
    date = Column(Date, nullable=False)

    # 사건 유형
    case_type = Column(String(20), nullable=False)

    # 죄명
    charge = Column(String(255), nullable=True)

    # 판결 결과
    result = Column(String(255), nullable=True)

    # 관련 법조문
    laws_referenced = Column(Text, nullable=True)

    # 판례 원문 텍스트
    content = Column(Text, nullable=False)

    # 수집 일시
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
