# 시각화 렌더링 서비스
# 판사 3명 결과 → 형사/민사 차트용 JSON 생성

import re
from app.backend.schemas.vis_render_schema import (
    CivilDecisionChart,
    CivilResponsibilityChart,
    CivilVisData,
    CriminalDecisionChart,
    CriminalSentenceChart,
    CriminalVisData,
    JudgeResult,
)
from app.com.logger import get_logger

logger = get_logger("vis_render_service")


def _extract_numeric(value: str) -> float:
    """
    판사 value 문자열에서 숫자 추출
    예) "징역 24개월" → 24.0 / "집행유예 12개월" → 12.0 / "70%" → 70.0
    """
    numbers = re.findall(r"\d+(?:\.\d+)?", value)
    if not numbers:
        return 0.0
    # 여러 숫자가 있으면 첫 번째 (주형량)
    return float(numbers[0])


def _detect_unit(value: str) -> str:
    """형량 단위 감지: 개월 | 원 | %"""
    if "원" in value:
        return "원"
    if "%" in value:
        return "%"
    return "개월"


### 형사 시각화 ###

def build_criminal_vis(judges: list[JudgeResult]) -> CriminalVisData:
    """형사 판결 → 유죄/무죄 비율 + 형량 범위 차트 생성"""
    guilty_count = sum(1 for j in judges if j.decision == "유죄")
    not_guilty_count = len(judges) - guilty_count
    total = len(judges) or 1

    values_by_judge = {j.judge_type: _extract_numeric(j.value) for j in judges}
    numeric_values = list(values_by_judge.values())
    unit = _detect_unit(judges[0].value) if judges else "개월"

    return CriminalVisData(
        decision_chart=CriminalDecisionChart(
            guilty_count=guilty_count,
            not_guilty_count=not_guilty_count,
            guilty_ratio=round(guilty_count / total, 2),
        ),
        sentence_chart=CriminalSentenceChart(
            unit=unit,
            min_value=min(numeric_values) if numeric_values else 0,
            max_value=max(numeric_values) if numeric_values else 0,
            avg_value=round(sum(numeric_values) / len(numeric_values), 1) if numeric_values else 0,
            values_by_judge=values_by_judge,
        ),
    )


### 민사 시각화 ###

def build_civil_vis(judges: list[JudgeResult]) -> CivilVisData:
    """민사 판결 → 인용/기각 비율 + 과실 비율 차트 생성"""
    upheld_count = sum(1 for j in judges if j.decision == "인용")
    dismissed_count = len(judges) - upheld_count
    total = len(judges) or 1

    values_by_judge = {j.judge_type: _extract_numeric(j.value) for j in judges}
    numeric_values = list(values_by_judge.values())

    return CivilVisData(
        decision_chart=CivilDecisionChart(
            upheld_count=upheld_count,
            dismissed_count=dismissed_count,
            upheld_ratio=round(upheld_count / total, 2),
        ),
        responsibility_chart=CivilResponsibilityChart(
            min_value=min(numeric_values) if numeric_values else 0,
            max_value=max(numeric_values) if numeric_values else 0,
            avg_value=round(sum(numeric_values) / len(numeric_values), 1) if numeric_values else 0,
            values_by_judge=values_by_judge,
        ),
    )


### 통합 진입점 ###

def build_vis_data(case_type: str, judges_raw: list[dict]) -> CriminalVisData | CivilVisData:
    """
    DB에서 꺼낸 judges JSON → 시각화 데이터 생성

    AI파트 연동 후에도 이 함수는 변경 불필요.
    judges_raw 구조만 AI파트 출력과 동일하면 됨.
    """
    judges = [JudgeResult(**j) for j in judges_raw]

    if case_type == "형사":
        return build_criminal_vis(judges)
    elif case_type == "민사":
        return build_civil_vis(judges)
    else:
        logger.warning(f"알 수 없는 사건 유형: {case_type}, 형사로 처리")
        return build_criminal_vis(judges)
