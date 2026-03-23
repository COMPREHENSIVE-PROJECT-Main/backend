# 사용자 입력 사건 데이터 생성 / json 파일 & DB 저장
import json
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.backend.models.user_case import UserCase
from app.backend.schemas.user_case_schema import CaseData, CaseResponse


# 사건 입력 파일 저장 경로
INPUT_CASES_DIR = Path("data/input_cases")


def _generate_case_id() -> str:
    """
    기존 저장된 파일 수를 기반으로 case_id 생성

    Returns:
        case_0001 형태 ID
    """

    # 디렉토리 없으면 생성
    INPUT_CASES_DIR.mkdir(parents=True, exist_ok=True)

    # 기존 JSON 파일 개수 카운트
    existing = list(INPUT_CASES_DIR.glob("*.json"))
    next_num = len(existing) + 1

    return f"case_{next_num:04d}"


def save_case(description: str, user_id: int, db: Session) -> CaseResponse:
    """
    사건 설명을 JSON 파일로 저장하고 DB에 유저-사건 연결 정보 기록

    Args:
        description: 검증된 사건 설명 텍스트
        user_id: 사건을 입력한 유저 ID
        db: DB 세션

    Returns:
        CaseResponse 객체
    """

    case_id = _generate_case_id()

    case_data = CaseData(
        case_id=case_id,
        description=description,
        created_at=date.today()
    )

    # JSON 파일로 저장
    file_path = INPUT_CASES_DIR / f"{case_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(case_data.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

    # DB에 유저-사건 연결 정보 저장
    user_case = UserCase(case_id=case_id, user_id=user_id)
    db.add(user_case)
    db.commit()

    return CaseResponse(case_id=case_id, user_id=user_id)
