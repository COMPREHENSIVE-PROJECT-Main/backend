# case 규격
from datetime import datetime, date

from pydantic import BaseModel, Field

# 사건 입력 요청 데이터
class CaseInput(BaseModel):
    case_description: str = Field(
        min_length=20,
        description="사건 설명 (최소 20자)"
    )

# case 저장 구조
class CaseData(BaseModel):
    case_id: str
    description: str
    created_at: date

    # DB 모델을 바로 넣어도 변환되도록 설정
    model_config = {"from_attributes": True}

# 사건 입력 성공 시 반환 데이터
class CaseResponse(BaseModel):
    case_id: str
    user_id: int
    message: str = "사건이 접수되었습니다."