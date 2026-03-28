# 사건 입력 API 입출력 규격
from datetime import date

from pydantic import BaseModel, Field


# 사건 입력 요청 데이터
class CaseInput(BaseModel):
    case_description: str = Field(
        min_length=20,
        description="사건 설명 (최소 20자)"
    )


# case 저장 구조 (JSON 파일 저장용)
class CaseData(BaseModel):
    case_id: str
    description: str
    created_at: date

    model_config = {"from_attributes": True}


# 사건 입력 성공 시 반환 데이터 (추가 질문 목록 포함)
class CaseResponse(BaseModel):
    case_id: str
    user_id: int
    questions: list[str]  # LLM이 요청한 추가 질문 목록 (없으면 빈 리스트)
    message: str = "사건이 접수되었습니다."


# 추가 정보 입력 요청 데이터
class CaseInputPlus(BaseModel):
    case_id: str
    additional_info: str = ""  # 추가 정보 없으면 빈 문자열


# 추가 정보 입력 성공 시 반환 데이터
class CaseInputPlusResponse(BaseModel):
    case_id: str
    message: str = "추가 정보가 저장되었습니다."
