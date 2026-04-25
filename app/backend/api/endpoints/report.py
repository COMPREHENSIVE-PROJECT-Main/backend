# 리포트 엔드포인트
# GET /api/report/{case_id}        — 종합 리포트 JSON 반환
# GET /api/report/{case_id}/export — HTML 렌더링용 전체 데이터 + 판결문 텍스트 반환
#                                    (PDF 생성은 프론트 HTML 템플릿 수령 후 추가)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.backend.models.report import Report
from app.backend.models.simulation import Simulation
from app.backend.models.user import User
from app.backend.models.user_case import UserCase
from app.backend.schemas.final_report_schema import ExportResponse, FinalReport
from app.backend.schemas.verdict_schema import VerdictDocument
from app.backend.services.final_report_service import get_or_create_report
from app.backend.utils.dependencies import get_current_user, get_db
from app.backend.utils.legal_formatter import format_verdict_text
from app.com.logger import get_logger

logger = get_logger("report_endpoint")

router = APIRouter(prefix="/report", tags=["report"])


def _get_verified_simulation(case_id: str, user_id: int, db: Session) -> Simulation:
    """소유권 검증 + 완료된 시뮬레이션 조회 공통 로직"""
    user_case = db.query(UserCase).filter(
        UserCase.case_id == case_id,
        UserCase.user_id == user_id,
    ).first()
    if not user_case:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 사건에 대한 접근 권한이 없습니다.",
        )

    simulation = (
        db.query(Simulation)
        .filter(
            Simulation.case_id == case_id,
            Simulation.user_id == user_id,
            Simulation.status == "completed",
        )
        .order_by(Simulation.created_at.desc())
        .first()
    )
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="완료된 시뮬레이션이 없습니다. 먼저 시뮬레이션을 실행하고 완료해주세요.",
        )

    return simulation


@router.get(
    "/{case_id}",
    response_model=FinalReport,
    summary="종합 리포트 조회",
    description=(
        "시뮬레이션 완료 후 판결문 · 공방 요약 · 판사 비교 · 차트 데이터를 통합 반환합니다. "
        "첫 요청 시 리포트를 생성하고 DB에 저장하며, 이후 요청은 저장된 데이터를 즉시 반환합니다. "
        "JWT 인증 필수, 본인 사건만 조회 가능합니다."
    ),
)
async def get_report(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinalReport:
    simulation = _get_verified_simulation(case_id, current_user.id, db)
    logger.info(f"리포트 요청: case_id={case_id}, user_id={current_user.id}")
    return get_or_create_report(case_id, current_user.id, simulation, db)


@router.get(
    "/{case_id}/export",
    response_model=ExportResponse,
    summary="리포트 내보내기 데이터 조회",
    description=(
        "HTML 템플릿 렌더링에 필요한 전체 리포트 데이터를 반환합니다. "
        "report 필드: 모든 구조화 데이터 (차트·판사비교·공방요약). "
        "verdict_text 필드: 법원 표준 양식 판결문 텍스트 (주문/이유/결론 구분선 포함). "
        "download_url 필드: PDF 생성 완료 후 다운로드 경로 (현재 null, HTML 템플릿 수령 후 활성화). "
        "JWT 인증 필수, 본인 사건만 조회 가능합니다."
    ),
)
async def export_report(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExportResponse:
    simulation = _get_verified_simulation(case_id, current_user.id, db)
    report = get_or_create_report(case_id, current_user.id, simulation, db)

    # 법원 표준 양식 텍스트 생성 (HTML 템플릿 없어도 텍스트 형식은 제공)
    verdict_doc = VerdictDocument(
        verdict_id=f"verdict_{case_id}",
        case_type=report.case_info.case_type,
        order=report.verdict.sentence,
        rationale=report.verdict.rationale,
        conclusion=report.verdict.conclusion,
        decision=report.verdict.decision,
        value=report.verdict.value,
    )
    verdict_text = format_verdict_text(verdict_doc)

    logger.info(f"리포트 내보내기 요청: case_id={case_id}, user_id={current_user.id}")

    # [PDF 플러그인 포인트]
    # HTML 템플릿 수령 후 아래 로직 추가:
    #   from app.backend.services.export_service import generate_pdf
    #   download_url = await generate_pdf(case_id, report, verdict_text)
    return ExportResponse(
        case_id=case_id,
        report=report,
        verdict_text=verdict_text,
        download_url=None,
    )
