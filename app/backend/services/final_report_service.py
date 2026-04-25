# 종합 리포트 생성 서비스
# 시뮬 완료 후 Phase 4 서비스들을 호출해서 FinalReport 생성 + DB 저장
# 첫 요청 시 생성 후 저장, 이후 요청은 DB에서 바로 반환 (캐시)

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.backend.models.report import Report
from app.backend.models.simulation import Simulation
from app.backend.schemas.final_report_schema import (
    CaseInfo,
    ChartData,
    DebateSummarySection,
    FinalReport,
    JudgeComparison,
    JudgeInfo,
    VerdictInfo,
)
from app.backend.services.gap_analysis_engine import analyze_gap
from app.backend.services.summary_refine_service import build_debate_summary
from app.backend.services.verdict_final_service import build_verdict_document
from app.backend.services.vis_render_service import build_vis_data
from app.backend.utils.viz_data_generator import (
    build_bar_chart_data,
    build_decision_pie_data,
    build_triangle_chart_data,
)
from app.com.logger import get_logger

logger = get_logger("final_report_service")

INPUT_CASES_DIR = Path("data/input_cases")

# 화자 → prosecution/defense 키 매핑
_SPEAKER_TO_ROLE = {
    "검사": "prosecution",
    "원고": "prosecution",
    "변호인": "defense",
    "피고": "defense",
}


def _load_case_json(case_id: str) -> dict:
    """data/input_cases/{case_id}.json 로드"""
    path = INPUT_CASES_DIR / f"{case_id}.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _infer_case_type(final_verdict: dict) -> str:
    """final_verdict.decision 으로 사건 유형 추론"""
    decision = final_verdict.get("decision", "")
    if decision in ("유죄", "무죄"):
        return "형사"
    return "민사"


def _reshape_rounds(rounds_flat: list[dict]) -> list[dict]:
    """
    DB에 저장된 flat rounds → build_debate_summary 입력 형식으로 변환

    flat (저장 형식):
        [{round: 1, speaker: "검사", argument: "...", evidence_refs: [...]}, ...]

    shaped (summary 기대 형식):
        [{round: 1, prosecution: {argument: ..., evidence_refs: [...]}, defense: {...}}, ...]
    """
    grouped: dict[int, dict] = {}
    for item in rounds_flat:
        round_no = item.get("round", 0)
        speaker = item.get("speaker", "")
        role = _SPEAKER_TO_ROLE.get(speaker, "prosecution")

        if round_no not in grouped:
            grouped[round_no] = {"round": round_no}

        grouped[round_no][role] = {
            "argument": item.get("argument", ""),
            "evidence_refs": item.get("evidence_refs", []),
        }

    return [grouped[k] for k in sorted(grouped.keys())]


def _build_report(case_id: str, simulation: Simulation) -> FinalReport:
    """시뮬 DB 데이터 + 사건 JSON → FinalReport 조립"""
    case_json = _load_case_json(case_id)
    final_verdict = simulation.final_verdict or {}

    # case_type: JSON 분석 결과 우선, 없으면 판결에서 추론
    case_type = (
        case_json.get("analysis", {}).get("case_type")
        or _infer_case_type(final_verdict)
    )

    # 사건 기본 정보
    case_info = CaseInfo(
        case_id=case_id,
        case_type=case_type,
        case_description=case_json.get("description", ""),
        created_at=str(case_json.get("created_at", "")),
    )

    # 선고 정보
    verdict_doc = build_verdict_document(case_id, case_type, final_verdict)
    verdict_info = VerdictInfo(
        sentence=verdict_doc.order,
        rationale=verdict_doc.rationale,
        conclusion=verdict_doc.conclusion,
        decision=verdict_doc.decision,
        value=verdict_doc.value,
    )

    # 판사 3인 비교 + 간극 분석
    judges_raw = list(simulation.judges)
    judge_list = [
        JudgeInfo(
            judge_type=j["judge_type"],
            decision=j["decision"],
            value=j["value"],
        )
        for j in judges_raw
    ]
    gap = analyze_gap(judges_raw)
    judge_comparison = JudgeComparison(judges=judge_list, gap=gap)

    # 차트 데이터
    vis_data = build_vis_data(case_type, judges_raw)
    chart_data = ChartData(
        decision_pie=build_decision_pie_data(vis_data),
        bar_chart=build_bar_chart_data(vis_data),
        triangle_chart=build_triangle_chart_data(gap),
    )

    # 공방 요약 (flat rounds → grouped 변환 후 처리)
    rounds_shaped = _reshape_rounds(list(simulation.rounds))
    debate = build_debate_summary(case_id, case_type, rounds_shaped)
    summary = DebateSummarySection(
        rounds=debate.rounds,
        key_issues=debate.key_issues,
    )

    return FinalReport(
        case_info=case_info,
        verdict=verdict_info,
        judge_comparison=judge_comparison,
        charts=chart_data,
        summary=summary,
    )


def get_or_create_report(
    case_id: str,
    user_id: int,
    simulation: Simulation,
    db: Session,
) -> FinalReport:
    """
    DB에 리포트가 있으면 바로 반환, 없으면 생성 후 저장 (지연 생성 + 캐시)

    AI파트 연동 후에도 이 함수는 변경 불필요.
    _build_report() 내부의 Phase 4 서비스들이 실제 AI 결과를 사용하도록 바뀌면 됨.
    """
    existing = db.query(Report).filter(Report.case_id == case_id).first()
    if existing:
        logger.info(f"캐시된 리포트 반환: case_id={case_id}")
        return FinalReport(**existing.report_data)

    report = _build_report(case_id, simulation)

    db_report = Report(
        case_id=case_id,
        user_id=user_id,
        report_data=report.model_dump(),
    )
    db.add(db_report)
    db.commit()

    logger.info(f"리포트 생성 및 저장: case_id={case_id}")
    return report
