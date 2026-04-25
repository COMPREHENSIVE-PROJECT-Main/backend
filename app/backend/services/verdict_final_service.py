# 판결문 확정 서비스
# 마스터 판사 데이터 → 법원 표준 양식 판결문 생성

from app.backend.schemas.verdict_schema import VerdictDocument
from app.com.logger import get_logger

logger = get_logger("verdict_final_service")

# 형사 표준 문구
_CRIMINAL_GUILTY = "피고인을 {value}에 처한다."
_CRIMINAL_NOT_GUILTY = "피고인은 무죄."

# 민사 표준 문구
_CIVIL_UPHELD = "피고는 원고에게 {value}의 책임을 진다."
_CIVIL_DISMISSED = "원고의 청구를 기각한다."


def _build_order(case_type: str, decision: str, value: str) -> str:
    """사건 유형 + 판결에 따른 주문 문구 생성"""
    if case_type == "형사":
        if decision == "유죄":
            return _CRIMINAL_GUILTY.format(value=value)
        return _CRIMINAL_NOT_GUILTY

    # 민사
    if decision == "인용":
        return _CIVIL_UPHELD.format(value=value)
    return _CIVIL_DISMISSED


def build_verdict_document(
    case_id: str,
    case_type: str,
    final_verdict: dict,
) -> VerdictDocument:
    """
    DB에서 꺼낸 final_verdict JSON → 법원 표준 양식 판결문 생성

    AI파트 연동 후에도 이 함수는 변경 불필요.
    final_verdict 구조만 AI파트 출력과 동일하면 됨.
    """
    decision = final_verdict.get("decision", "")
    value = final_verdict.get("value", "")
    rationale = final_verdict.get("rationale", "")
    conclusion = final_verdict.get("conclusion", "")

    # order가 이미 있으면 그대로, 없으면 표준 문구 생성
    order = final_verdict.get("order") or _build_order(case_type, decision, value)

    verdict_id = f"verdict_{case_id}"

    logger.info(f"판결문 생성: verdict_id={verdict_id}, decision={decision}")

    return VerdictDocument(
        verdict_id=verdict_id,
        case_type=case_type,
        order=order,
        rationale=rationale,
        conclusion=conclusion[:200],  # 200자 제한
        decision=decision,
        value=value,
    )
