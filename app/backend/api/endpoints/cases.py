# 사건 입력 관련 엔드포인트
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.backend.utils.dependencies import get_current_user, get_db
from app.backend.models.user import User
from app.backend.schemas.user_case_schema import CaseInput, CaseInputPlus, CaseInputPlusResponse, CaseResponse
from app.backend.services.user_case_service import save_case, save_case_plus
from app.backend.utils.case_input_validator import validate_case_input
from app.com.logger import get_logger

logger = get_logger("user_case")

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/input", response_model=CaseResponse)
async def input_case(
    case_input: CaseInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사건 설명 입력 수신

    - JWT 유저 확인
    - 입력값 검증 (최소 20자, 공백 확인)
    - JSON 파일 저장 + DB 저장
    - 응답에 추가 정보 요청 질문 목록 포함 (questions)
    """

    # 입력값 검증 및 공백 제거
    validated_description = validate_case_input(case_input.case_description)

    # 사건 저장 및 추가 질문 생성
    return await save_case(
        description=validated_description,
        user_id=current_user.id,
        db=db
    )


@router.post("/input_plus", response_model=CaseInputPlusResponse)
async def input_case_plus(
    case_input: CaseInputPlus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    추가 정보 입력 수신

    - JWT 유저 확인
    - case_id 소유권 검증 (본인 사건인지 확인)
    - 기존 사건 JSON에 추가 정보 병합 저장
    - additional_info가 빈 문자열이면 추가 정보 없음으로 저장
    """

    return await save_case_plus(
        case_id=case_input.case_id,
        additional_info=case_input.additional_info,
        user_id=current_user.id,
        db=db
    )
