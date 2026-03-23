# case 관련 엔드포인트
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.backend.utils.dependencies import get_current_user, get_db
from app.backend.models.user import User
from app.schemas.user_case_schema import CaseInput, CaseResponse
from app.services.user_case_service import save_case
from app.backend.utils.case_input_validator import validate_case_input
from app.com.logger import get_logger

logger = get_logger("user_case")

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/input", response_model = CaseResponse)
async def input_case(
    case_input: CaseInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사건 설명 입력 수신

    - JWT 유저확인
    - 입력값 검증 (최소 20자, 공백 확인)
    - JSON 파일 저장 + DB 저장

    """

    # 입력값 검증 및 공백 제거
    validated_description = validate_case_input(case_input.case_description)

    # 사건 저장
    return save_case(
        description = validated_description,
        user_id = current_user.id,
        db = db
    )