# 국가법령정보 API에서 수집한 법령 조문 테이블
from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, func

from app.database import Base


class Statutes(Base):
    __tablename__ = "statutes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 법령명 (예: 도로교통법)
    law_name = Column(String(200), nullable=False)

    # 조문 번호 (예: 제44조)
    article_number = Column(String(50), nullable=False)

    # 조문 제목
    article_title = Column(String(200), nullable=True)

    # 조문 전체 내용
    article_content = Column(Text, nullable=False)

    # 형사 / 민사 / 행정 / 특별법
    category = Column(String(50), nullable=False)

    effective_date = Column(Date, nullable=True)

    source_url = Column(String(500), nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
