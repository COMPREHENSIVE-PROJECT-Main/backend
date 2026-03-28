# 사건 분석 결과 API 입출력 규격

from pydantic import BaseModel


# 증거 항목
class Evidence(BaseModel):
    type: str         # 증거 유형 (예: "CCTV", "목격자 진술", "진단서")
    description: str  # 증거 설명


# LLM 분석 결과 구조 (data/input_cases/{case_id}.json의 analysis 필드로 저장)
class AnalysisResult(BaseModel):
    case_type: str           # "형사" | "민사"
    main_action: str         # 주요 행위 (예: "음주운전")
    victim_exist: bool       # 피해자 존재 여부
    injury_level: str        # 피해 정도 (예: "경미한 부상", "사망")
    evidence: list[Evidence] # 추출된 증거 목록


# 분석 완료 응답
class AnalysisResponse(BaseModel):
    case_id: str
    case_type: str
    main_action: str
    victim_exist: bool
    injury_level: str
    evidence: list[Evidence]
    message: str = "분석이 완료되었습니다."
