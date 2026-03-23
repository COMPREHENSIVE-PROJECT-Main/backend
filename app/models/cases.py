# 판례 데이터를 저장하는 cases 테이블 모델
from sqlalchemy import Column, String, Text, Date, SmallInteger, TIMESTAMP, func

from app.database import Base


class Cases(Base):
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
    case_type = Column(String(20), nullable=True)

    # 죄명
    charge = Column(String(255), nullable=True)

    # 판결 결과
    result = Column(String(255), nullable=True)

    # 원고
    plaintiff = Column(Text, nullable=True)

    # 피고
    defendant = Column(Text, nullable=True)

    # 판결 요지
    ruling_summary = Column(Text, nullable=True)

    # 관련 법조문
    laws_referenced = Column(Text, nullable=True)

    # 판례 원문 텍스트
    content = Column(Text, nullable=False)

    # 출처 (aihub_v1 / aihub_v2 / law_api / court_portal)
    source = Column(String(20), nullable=False)

    # 출처 우선순위 (1: 최우선 ~ 4)
    source_priority = Column(SmallInteger, nullable=False)

    # 수집 일시
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
