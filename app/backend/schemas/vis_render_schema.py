# 시각화 렌더링 API 입출력 규격
from typing import Literal
from pydantic import BaseModel


### 공통 ###

# 판사별 판결 요약 (시각화 입력용)
class JudgeResult(BaseModel):
    judge_type: Literal["원칙판사", "형평판사", "여론판사"]
    decision: str       # "유죄" | "무죄" | "인용" | "기각"
    value: str          # 형사: "징역 24개월" / 민사: "70%"
    rationale: str


### 형사 시각화 ###

# 형사 판결 분포 (유죄/무죄 비율)
class CriminalDecisionChart(BaseModel):
    guilty_count: int           # 유죄 판사 수
    not_guilty_count: int       # 무죄 판사 수
    guilty_ratio: float         # 유죄 비율 (0.0 ~ 1.0)

# 형사 형량 범위 차트
class CriminalSentenceChart(BaseModel):
    unit: Literal["개월", "원"]  # 징역 = 개월, 벌금 = 원
    min_value: float            # 최소 형량
    max_value: float            # 최대 형량
    avg_value: float            # 평균 형량
    values_by_judge: dict[str, float]  # { "원칙판사": 24, "형평판사": 12, ... }

# 형사 시각화 통합
class CriminalVisData(BaseModel):
    case_type: Literal["형사"] = "형사"
    decision_chart: CriminalDecisionChart
    sentence_chart: CriminalSentenceChart


### 민사 시각화 ###

# 민사 판결 분포 (인용/기각 비율)
class CivilDecisionChart(BaseModel):
    upheld_count: int           # 인용 판사 수
    dismissed_count: int        # 기각 판사 수
    upheld_ratio: float         # 인용 비율 (0.0 ~ 1.0)

# 민사 과실 비율 차트
class CivilResponsibilityChart(BaseModel):
    unit: Literal["%"] = "%"
    min_value: float            # 최소 과실 비율
    max_value: float            # 최대 과실 비율
    avg_value: float            # 평균 과실 비율
    values_by_judge: dict[str, float]  # { "원칙판사": 70.0, ... }

# 민사 시각화 통합
class CivilVisData(BaseModel):
    case_type: Literal["민사"] = "민사"
    decision_chart: CivilDecisionChart
    responsibility_chart: CivilResponsibilityChart


### 간극 분석 ###

# 판사 간 수치 차이 (Delta)
class GapAnalysis(BaseModel):
    delta_principle_equity: float   # 원칙판사 - 형평판사
    delta_equity_opinion: float     # 형평판사 - 여론판사
    delta_principle_opinion: float  # 원칙판사 - 여론판사
    unit: str                       # "개월" | "원" | "%"


### 최종 응답 ###

class VisRenderResponse(BaseModel):
    case_id: str
    case_type: str
    vis_data: CriminalVisData | CivilVisData
    gap_analysis: GapAnalysis
