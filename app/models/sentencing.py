# 대법원 양형위원회에서 수집한 법죄별 형량기준 테이블
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func

from app.database import Base


class Sentencing(Base):
    __tablename__ = "sentencing"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 범죄군 (예: 교통범죄)
    crime_type = Column(String(50), nullable=False)

    # 세부 범죄 (예: 음주운전)
    sub_type = Column(String(100), nullable=False)

    # 최소 형량
    sentencing_min = Column(String(20), nullable=False)

    # 최대 형량
    sentencing_max = Column(String(20), nullable=False)

    # 기본 / 가중 / 감경
    sentencing_type = Column(String(20), nullable=False)

    # 가중 요소
    aggravating = Column(Text, nullable=True)

    # 감경 요소
    mitigating = Column(Text, nullable=True)

    # 집행유예 기준
    probation_criteria = Column(Text, nullable=True)

    source_url = Column(String(500), nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
