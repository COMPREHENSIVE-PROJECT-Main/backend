# 시뮬레이션 결과 저장 테이블
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB

from app.backend.db.database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), ForeignKey("user_cases.case_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # "in_progress" | "completed" | "failed"
    status = Column(String(20), nullable=False, default="in_progress")

    # 라운드별 공방 결과 누적 저장
    rounds = Column(JSONB, nullable=False, default=list)

    # 판사 3명 판결 누적 저장
    judges = Column(JSONB, nullable=False, default=list)

    # 마스터 판사 최종 판결
    final_verdict = Column(JSONB, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
