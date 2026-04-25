# 종합 리포트 저장 테이블
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB

from app.backend.db.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 사건 ID (1사건당 1리포트, unique)
    case_id = Column(String(50), ForeignKey("user_cases.case_id"), nullable=False, unique=True)

    # 리포트를 생성한 유저
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 전체 리포트 JSON (Phase 4 서비스 결과 통합)
    report_data = Column(JSONB, nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
