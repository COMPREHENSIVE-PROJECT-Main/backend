# case 입력 검증
from fastapi import HTTPException

from app.com.logger import get_logger

logger = get_logger("case_input_validator")

def validate_case_input(text: str) -> str:
    """
    사건 설명 텍스트 유효성 검증

    Args:
        text: 사용자가 입력한 사건 설명 원문

    Returns:
        공백 제거된 사건 설명 텍스트

    Raises:
        HTTPException 400: 빈 입력 또는 20자 미만일 경우
    """

    # 앞뒤 공백 제거
    cleaned = text.strip()

    # 공백만 입력한 경우 차단
    if not cleaned:
        raise HTTPException(
            status_code=400,
            detail="사건 설명을 입력해주세요."
        )

    # 최소 글자 수 미달 차단
    if len(cleaned) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"사건 설명은 최소 20자 이상 입력해주세요. (현재 {len(cleaned)}자)"
        )

    return cleaned
