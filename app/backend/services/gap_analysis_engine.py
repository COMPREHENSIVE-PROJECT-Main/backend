# 판사 간 간극 분석 서비스
# 법리(원칙) / 형평 / 여론 판사 수치 차이 계산

from app.backend.schemas.vis_render_schema import GapAnalysis, JudgeResult
from app.backend.services.vis_render_service import _detect_unit, _extract_numeric
from app.com.logger import get_logger

logger = get_logger("gap_analysis")

# 판사 타입 → 키 매핑
_JUDGE_KEY = {
    "원칙판사": "principle",
    "형평판사": "equity",
    "여론판사": "opinion",
}


def analyze_gap(judges_raw: list[dict]) -> GapAnalysis:
    """
    판사 3명의 수치 차이(Delta) 계산

    Delta 계산식:
    - delta_principle_equity  = 원칙판사 - 형평판사
    - delta_equity_opinion    = 형평판사 - 여론판사
    - delta_principle_opinion = 원칙판사 - 여론판사

    AI파트 연동 후에도 이 함수는 변경 불필요.
    judges_raw 구조만 AI파트 출력과 동일하면 됨.
    """
    judges = [JudgeResult(**j) for j in judges_raw]

    values: dict[str, float] = {}
    unit = "개월"

    for judge in judges:
        key = _JUDGE_KEY.get(judge.judge_type)
        if key:
            values[key] = _extract_numeric(judge.value)
            unit = _detect_unit(judge.value)

    principle = values.get("principle", 0.0)
    equity = values.get("equity", 0.0)
    opinion = values.get("opinion", 0.0)

    return GapAnalysis(
        delta_principle_equity=round(principle - equity, 2),
        delta_equity_opinion=round(equity - opinion, 2),
        delta_principle_opinion=round(principle - opinion, 2),
        unit=unit,
    )
