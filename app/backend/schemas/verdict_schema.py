# 판결문 API 입출력 규격 (법원 표준 양식)
from typing import Literal
from pydantic import BaseModel, Field


class VerdictDocument(BaseModel):
    verdict_id: str
    case_type: Literal["형사", "민사"]
    order: str          # 주문
    rationale: str      # 이유
    conclusion: str     # 결론 (200자 이내)
    decision: str       # "유죄" | "무죄" | "인용" | "기각"
    value: str          # 최종 형량 또는 책임 비율
