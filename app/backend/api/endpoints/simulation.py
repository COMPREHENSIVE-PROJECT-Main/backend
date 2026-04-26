# 공방 시뮬레이션 엔드포인트
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.backend.db.session import get_db
from app.backend.models.user import User
from app.backend.models.user_case import UserCase
from app.backend.schemas.simulation_schema import SimulationStartRequest
from app.backend.services.simulation_orchestrator import run_simulation
from app.backend.services.simulation_service import get_simulation
from app.backend.utils.dependencies import get_current_user
from app.com.logger import get_logger

logger = get_logger("simulation")

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post(
    "/start",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "SSE 스트림",
            "content": {"text/event-stream": {"example": "event: simulation_start\ndata: {\"case_id\": \"case_0001\", \"case_type\": \"형사\", \"total_rounds\": 3}\n\n"}},
        }
    },
)
async def start_simulation(
    request: SimulationStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SSE(text/event-stream) 스트림 반환. Swagger에서 실시간 확인 불가, fetch API로 연동.

    이벤트 순서:
    simulation_start → [round_start → token(반복) → round_end] × N → judge_decision(×3) → final_verdict → simulation_end

    각 이벤트 data 구조:
    - simulation_start: { case_id, case_type, total_rounds }
    - round_start: { round, speaker, speaker_role }
    - token: { text }
    - round_end: { round, speaker, argument, evidence_refs }
    - judge_decision: { judge_type, decision, value, rationale }
    - final_verdict: { decision, value, order, rationale, conclusion }
    - simulation_end: { case_id, message }
    - error: { code, message, failed_at_round } ← 재시도 시 start_from_round로 사용

    시뮬 확인 curl
    curl -N -X POST http://localhost:8080/api/simulation/start \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer 복붙" \
    -d '{"case_id": "case_0001"}'
    """
    # case_id 소유권 검증 (JWT 유저 기준)
    user_case = db.query(UserCase).filter(
        UserCase.case_id == request.case_id,
        UserCase.user_id == current_user.id
    ).first()

    if not user_case:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 사건에 대한 접근 권한이 없습니다."
        )

    logger.info(f"시뮬레이션 요청: user_id={current_user.id}, case_id={request.case_id}, start_from_round={request.start_from_round}")

    return StreamingResponse(
        run_simulation(
            case_id=request.case_id,
            case_type=request.case_type,
            user_id=current_user.id,
            db=db,
            start_from_round=request.start_from_round,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # nginx 버퍼링 비활성화 (프록시 환경 대응)
        }
    )


@router.get("/{case_id}")
async def get_simulation_result(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    저장된 시뮬레이션 결과 조회

    - 가장 최근 시뮬레이션 결과 반환
    - status: "in_progress" | "completed" | "failed"
    """
    # case_id 소유권 검증
    user_case = db.query(UserCase).filter(
        UserCase.case_id == case_id,
        UserCase.user_id == current_user.id
    ).first()

    if not user_case:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 사건에 대한 접근 권한이 없습니다."
        )

    simulation = get_simulation(db=db, case_id=case_id, user_id=current_user.id)

    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시뮬레이션 결과가 없습니다."
        )

    return {
        "simulation_id": simulation.id,
        "case_id": simulation.case_id,
        "status": simulation.status,
        "rounds": simulation.rounds,
        "judges": simulation.judges,
        "final_verdict": simulation.final_verdict,
        "created_at": simulation.created_at,
        "updated_at": simulation.updated_at,
    }


"""
시뮬 확인 curl
curl -N -X POST http://localhost:8080/api/simulation/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 복붙" \
  -d '{"case_id": "case_0001", "case_type": "형사"}'
"""
