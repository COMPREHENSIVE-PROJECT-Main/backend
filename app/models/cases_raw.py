# 4개 소스에서 수집한 판례 원본을 그대로 쌓는 테이블 (중복 포함)
from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, func

from app.database import Base


class CasesRaw(Base):
    __tablename__ = "cases_raw"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 소스 원본 사건번호
    raw_case_id = Column(String(100), nullable=False)

    case_name = Column(String(255), nullable=True)

    court = Column(String(100), nullable=True)

    date = Column(Date, nullable=True)

    case_type = Column(String(20), nullable=True)

    charge = Column(String(255), nullable=True)

    result = Column(String(255), nullable=True)

    plaintiff = Column(Text, nullable=True)

    defendant = Column(Text, nullable=True)

    ruling_summary = Column(Text, nullable=True)

    laws_referenced = Column(Text, nullable=True)
    
    content = Column(Text, nullable=False)

    # 출처 (aihub_v1 / aihub_v2 / law_api / court_portal)
    source = Column(String(20), nullable=False)

    collected_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
