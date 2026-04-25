# 공방 요약 API 입출력 규격
from pydantic import BaseModel


# 라운드별 요약 항목
class RoundSummary(BaseModel):
    round_no: int
    speaker: str        # 형사: "검사" | "변호인" / 민사: "원고" | "피고"
    content: str        # 요약 내용
    law_refs: list[str] # 인용 법조문 / 판례


# 공방 전체 요약
class DebateSummary(BaseModel):
    case_id: str
    case_type: str
    rounds: list[RoundSummary]
    key_issues: list[str]   # 핵심 쟁점 상위 3~5개
    other_issues: str = "기타 쟁점"  # 나머지 쟁점 통합 문구
