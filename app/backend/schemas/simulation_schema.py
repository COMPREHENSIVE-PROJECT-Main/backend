# 공방 시뮬레이션 API 입출력 규격 및 SSE 이벤트 데이터 구조

from typing import Literal
from pydantic import BaseModel


# 요청 스키마

# 시뮬레이션 시작 요청
class SimulationStartRequest(BaseModel):
    case_id: str


# SSE 이벤트 데이터 스키마
# 각 클래스는 SSE data 필드에 JSON으로 직렬화되어 전송됨

# 시뮬 시작 알림
class SimulationStartData(BaseModel):
    case_id: str
    case_type: str          # "형사" | "민사"
    total_rounds: int       # 총 라운드 수 (기본 3)


# 라운드 시작 알림 (누가 말할 차례인지)
class RoundStartData(BaseModel):
    round: int
    speaker: str            # 형사: "검사" | "변호인" / 민사: "원고" | "피고"
    speaker_role: str       # "prosecution" | "defense"


# 텍스트 청크 (타이핑 효과용)
class TokenData(BaseModel):
    text: str


# 라운드 종료 (전체 주장 + 증거 refs)
class RoundEndData(BaseModel):
    round: int
    speaker: str
    argument: str           # 해당 라운드의 전체 주장
    evidence_refs: list[str]  # 인용 법조문 또는 판례 목록


# 판사 판결 (원칙 / 형평 / 여론 판사 각각 발행)
class JudgeDecisionData(BaseModel):
    judge_type: Literal["원칙판사", "형평판사", "여론판사"]
    decision: str           # "유죄" | "무죄" | "인용" | "기각"
    value: str              # 형사: "24개월" / 민사: "70%"
    rationale: str          # 판결 근거


# 마스터 판사 최종 판결
class FinalVerdictData(BaseModel):
    decision: str           # "유죄" | "무죄" | "인용" | "기각"
    value: str              # 최종 형량 또는 책임 비율
    order: str              # 주문
    rationale: str          # 판결 이유
    conclusion: str         # 최종 법리적 판단 요약 (200자 이내)


# 시뮬 종료 알림
class SimulationEndData(BaseModel):
    case_id: str
    message: str = "시뮬레이션이 완료되었습니다."


# 에러 알림
class SimulationErrorData(BaseModel):
    code: str
    message: str
